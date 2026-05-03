import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from weasyprint import HTML

from trades.models import BusinessProfile
from trades.views import testimonial_token_for_booking

from .forms import InvoiceCreateForm, InvoiceManageForm
from .models import Invoice, InvoiceImage, InvoiceProduct

logger = logging.getLogger(__name__)


def _get_active_business():
    return BusinessProfile.objects.filter(is_active=True).first()


class CreateInvoiceView(View):
    def get(self, request):
        form = InvoiceCreateForm()
        return render(request, "invoice/create.html", {"form": form})

    def post(self, request):
        form = InvoiceCreateForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.business = _get_active_business()
            invoice.save()
            messages.success(
                request,
                "Invoice draft created. The team will review and send it to you.",
            )
            return redirect("invoice_create")
        return render(request, "invoice/create.html", {"form": form})


@method_decorator(staff_member_required, name="dispatch")
class ManageInvoiceView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(
            Invoice.objects.prefetch_related("images", "products"), pk=pk
        )
        form = InvoiceManageForm(instance=invoice)
        context = self._build_context(invoice, form)
        return render(request, "invoice/manage.html", context)

    def post(self, request, pk):
        invoice = get_object_or_404(
            Invoice.objects.prefetch_related("images", "products"), pk=pk
        )
        status_before = invoice.status
        form = InvoiceManageForm(request.POST, request.FILES, instance=invoice)
        if form.is_valid():
            invoice = form.save()

            if form.cleaned_data.get("new_before_image"):
                self._add_image(
                    invoice, "before", form.cleaned_data["new_before_image"]
                )
            if form.cleaned_data.get("new_after_image"):
                self._add_image(
                    invoice, "after", form.cleaned_data["new_after_image"]
                )

            self._delete_marked_images(invoice, request.POST)
            self._save_products(invoice, request.POST)

            if (
                invoice.status == "sent"
                and status_before != "sent"
                and invoice.sent_at is None
            ):
                if not invoice.client_email:
                    messages.error(
                        request,
                        "Cannot send invoice: client email address is missing. "
                        "Please add an email address and save again.",
                    )
                else:
                    self._send_invoice_email(request, invoice)
                    invoice.sent_at = timezone.now()
                    invoice.save(update_fields=["sent_at"])

            messages.success(request, "Invoice updated.")
            return redirect("invoice_manage", pk=invoice.pk)

        context = self._build_context(invoice, form)
        return render(request, "invoice/manage.html", context)

    def _send_invoice_email(self, request, invoice):
        business = invoice.business or _get_active_business()
        business_name = business.business_name if business else "FlowPro Plumbing"
        business_phone = business.phone_display if business else ""
        business_email = business.email if business else ""

        testimonial_url = ""
        if invoice.booking_enquiry:
            token = testimonial_token_for_booking(invoice.booking_enquiry)
            path = reverse("testimonial_put", kwargs={"token": token})
            testimonial_url = request.build_absolute_uri(path)

        context = {
            "invoice": invoice,
            "business_name": business_name,
            "business_phone": business_phone,
            "business_email": business_email,
            "testimonial_url": testimonial_url,
        }

        subject = (
            f"Invoice {invoice.invoice_number} from {business_name}"
        )
        text_body = render_to_string(
            "invoice/emails/invoice_email.txt", context
        )
        html_body = render_to_string(
            "invoice/emails/invoice_email.html", context
        )

        pdf_html = render_to_string("invoice/pdf.html", {
            "invoice": invoice,
            "business_name": business_name,
        })
        pdf_bytes = HTML(string=pdf_html).write_pdf()

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.client_email],
        )
        message.attach_alternative(html_body, "text/html")
        message.attach(
            f"{invoice.invoice_number}.pdf", pdf_bytes, "application/pdf"
        )

        try:
            message.send(fail_silently=False)
            messages.success(
                request,
                f"Invoice {invoice.invoice_number} sent to {invoice.client_email}.",
            )
        except Exception:
            logger.exception(
                "Failed to send invoice email for invoice %s.", invoice.pk
            )
            messages.error(
                request,
                "Invoice saved but email delivery failed. Please try resending.",
            )

    def _add_image(self, invoice, image_type, image_file):
        count = invoice.images.filter(image_type=image_type).count()
        if count >= 3:
            messages.warning(request=None)
            return
        InvoiceImage.objects.create(
            invoice=invoice,
            image=image_file,
            image_type=image_type,
            sort_order=count,
        )

    def _delete_marked_images(self, invoice, post_data):
        for key in post_data:
            if key.startswith("delete_image_"):
                try:
                    image_id = int(key.split("_")[-1])
                    InvoiceImage.objects.filter(
                        id=image_id, invoice=invoice
                    ).delete()
                except (ValueError, IndexError):
                    pass

    def _save_products(self, invoice, post_data):
        existing_ids = set(invoice.products.values_list("id", flat=True))
        submitted_ids = set()

        i = 0
        while f"product_id_{i}" in post_data or f"product_name_{i}" in post_data:
            prod_id = post_data.get(f"product_id_{i}", "")
            name = post_data.get(f"product_name_{i}", "").strip()
            serial = post_data.get(f"product_serial_{i}", "").strip()
            price = post_data.get(f"product_price_{i}", "0").strip() or "0"
            qty = post_data.get(f"product_qty_{i}", "1").strip() or "1"
            warranty = post_data.get(f"product_warranty_{i}", "").strip()
            deleted = post_data.get(f"delete_product_{i}", "")

            if deleted or not name:
                i += 1
                continue

            price = self._parse_decimal(price)
            qty = self._parse_int(qty, 1)

            if prod_id and int(prod_id) in existing_ids:
                InvoiceProduct.objects.filter(id=int(prod_id)).update(
                    product_name=name,
                    serial_number=serial,
                    unit_price=price,
                    quantity=qty,
                    warranty_info=warranty,
                )
                submitted_ids.add(int(prod_id))
            else:
                prod = InvoiceProduct.objects.create(
                    invoice=invoice,
                    product_name=name,
                    serial_number=serial,
                    unit_price=price,
                    quantity=qty,
                    warranty_info=warranty,
                )
                submitted_ids.add(prod.pk)

            i += 1

        to_delete = existing_ids - submitted_ids
        if to_delete:
            InvoiceProduct.objects.filter(id__in=to_delete).delete()

    def _parse_decimal(self, value):
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return 0

    def _parse_int(self, value, default=1):
        try:
            v = int(value)
            return v if v > 0 else default
        except (ValueError, TypeError):
            return default

    def _build_context(self, invoice, form):
        booking_images = []
        if invoice.booking_enquiry:
            booking_images = invoice.booking_enquiry.diagnostic_images.all()
        return {
            "form": form,
            "invoice": invoice,
            "before_images": invoice.images.filter(image_type="before"),
            "after_images": invoice.images.filter(image_type="after"),
            "products": invoice.products.all(),
            "booking_images": booking_images,
        }
