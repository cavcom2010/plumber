import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.core import signing
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from .decorators import rate_limit
from .forms import BookingEnquiryForm, TestimonialSubmissionForm
from .models import (
    BookingEnquiry,
    BookingImage,
    BusinessProfile,
    LegalPage,
    ServiceOffering,
    Testimonial,
)
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)
TESTIMONIAL_LINK_SALT = "trades.testimonial-link"
TESTIMONIAL_LINK_MAX_AGE = 60 * 60 * 24 * 180


def testimonial_token_for_booking(booking):
    return signing.dumps({"booking_id": booking.pk}, salt=TESTIMONIAL_LINK_SALT)


def _site_context(extra=None):
    business = (
        BusinessProfile.objects.filter(is_active=True)
        .prefetch_related(
            "trust_indicators",
            "service_offerings",
            "testimonials",
            "legal_pages",
        )
        .first()
    )
    context = {
        "business": business,
        "trust_indicators": [],
        "service_offerings": [],
        "testimonials": [],
        "footer_pages": [],
        "mobile_menu_pages": [],
    }
    if business:
        context.update(
            {
                "trust_indicators": business.trust_indicators.filter(is_active=True),
                "service_offerings": business.service_offerings.filter(is_active=True),
                "testimonials": business.testimonials.filter(is_active=True),
                "footer_pages": business.legal_pages.filter(
                    is_active=True, show_in_footer=True
                ),
                "mobile_menu_pages": business.legal_pages.filter(
                    is_active=True, show_in_mobile_menu=True
                ),
            }
        )
    if extra:
        context.update(extra)
    return context


def trades_home(request):
    return render(request, "trades/home.html", _site_context())


def trades_services(request):
    return render(request, "trades/services.html", _site_context())


def trades_service_detail(request, slug):
    business = BusinessProfile.objects.filter(is_active=True).first()
    if not business:
        raise Http404("Service not found.")
    service = get_object_or_404(
        ServiceOffering,
        business=business,
        slug=slug,
        is_active=True,
    )
    other_services = (
        business.service_offerings.filter(is_active=True)
        .exclude(pk=service.pk)
        .order_by("sort_order", "title")
    )
    breadcrumbs = [
        {"label": "Home", "url": reverse("trades_home")},
        {"label": "Services", "url": reverse("trades_services")},
        {"label": service.title, "url": None},
    ]
    return render(
        request,
        "trades/service_detail.html",
        _site_context(
            {
                "service": service,
                "other_services": other_services,
                "breadcrumbs": breadcrumbs,
            }
        ),
    )


def trades_about(request):
    return render(request, "trades/about.html", _site_context())


def trades_reviews(request):
    return render(request, "trades/reviews.html", _site_context())


def robots_txt(request):
    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    sitemap_url = f"{scheme}://{host}" + reverse("sitemap")
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {sitemap_url}\n"
    )
    return HttpResponse(content, content_type="text/plain")


def trades_legal_page(request, slug):
    business = BusinessProfile.objects.filter(is_active=True).first()
    if not business:
        raise Http404("Page not found.")
    page = get_object_or_404(
        LegalPage,
        business=business,
        slug=slug,
        is_active=True,
    )
    breadcrumbs = [
        {"label": "Home", "url": reverse("trades_home")},
        {"label": page.title, "url": None},
    ]
    return render(
        request,
        "trades/legal_page.html",
        _site_context({"page": page, "breadcrumbs": breadcrumbs}),
    )


@rate_limit("BOOKING_RATE_LIMIT")
def trades_booking(request):
    if request.method == "POST":
        if getattr(request, "_rate_limited", False):
            form = BookingEnquiryForm()
            return render(request, "trades/booking.html", _site_context({
                "form": form,
                "rate_limited": True,
            }), status=429)

        form = BookingEnquiryForm(request.POST, request.FILES)
        if form.is_valid():
            booking = form.save()
            for i in range(1, 4):
                img = form.cleaned_data.get(f"diagnostic_image_{i}")
                if img:
                    BookingImage.objects.create(
                        booking=booking,
                        image=img,
                        sort_order=i - 1,
                    )
            _send_booking_notification(request, booking)
            _send_booking_confirmation(request, booking)
            _send_whatsapp_notification(request, booking)
            messages.success(
                request,
                "Booking enquiry received. We will call back to confirm availability.",
            )
            return redirect("trades_booking")
    else:
        form = BookingEnquiryForm()

    return render(request, "trades/booking.html", _site_context({"form": form}))


@rate_limit("BOOKING_RATE_LIMIT")
def testimonial_put(request, token):
    booking = _booking_from_testimonial_token(token)
    business = BusinessProfile.objects.filter(is_active=True).first()
    existing = getattr(booking, "submitted_testimonial", None)

    if request.method == "POST":
        if getattr(request, "_rate_limited", False):
            form = TestimonialSubmissionForm()
            return render(request, "trades/testimonial_put.html", _site_context({
                "form": form,
                "rate_limited": True,
            }), status=429)
        if existing:
            messages.success(request, "Your testimonial has already been received. Thank you.")
            return redirect("testimonial_put", token=token)

        form = TestimonialSubmissionForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.business = business or BusinessProfile.objects.filter(is_active=True).first()
            if testimonial.business is None:
                testimonial.business = BusinessProfile.objects.create()
            testimonial.source_booking = booking
            testimonial.job_label = booking.testimonial_job_display
            testimonial.author_label = "Verified Customer"
            testimonial.is_active = False
            testimonial.save()
            messages.success(
                request,
                "Thank you. Your testimonial has been sent and will appear after review.",
            )
            return redirect("testimonial_put", token=token)
    else:
        form = TestimonialSubmissionForm(
            initial={
                "author_name": booking.full_name,
                "rating": 5,
            }
        )

    return render(
        request,
        "trades/testimonial_put.html",
        _site_context(
            {
                "form": form,
                "booking": booking,
                "existing_testimonial": existing,
            }
        ),
    )


def _booking_from_testimonial_token(token):
    try:
        data = signing.loads(
            token,
            salt=TESTIMONIAL_LINK_SALT,
            max_age=TESTIMONIAL_LINK_MAX_AGE,
        )
    except signing.SignatureExpired as exc:
        raise Http404("This testimonial link has expired.") from exc
    except signing.BadSignature as exc:
        raise Http404("This testimonial link is invalid.") from exc

    booking_id = data.get("booking_id")
    if not booking_id:
        raise Http404("This testimonial link is invalid.")
    return get_object_or_404(BookingEnquiry, pk=booking_id)


def _send_booking_notification(request, booking):
    recipient = settings.ADMIN_NOTIFICATION_EMAIL
    if not recipient:
        logger.warning("ADMIN_NOTIFICATION_EMAIL is not configured; booking email skipped.")
        return

    context = _site_context({"booking": booking, "request": request})
    business_name = (
        context["business"].business_name if context.get("business") else "Your Local Tradesperson"
    )
    subject = (
        f"New booking from {business_name}: "
        f"{booking.get_service_display()} - {booking.postcode}"
    )
    text_body = render_to_string("trades/emails/booking_notification.txt", context)
    html_body = render_to_string("trades/emails/booking_notification.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send booking notification for enquiry %s.", booking.pk)


def _send_booking_confirmation(request, booking):
    if not booking.email:
        return
    business = BusinessProfile.objects.filter(is_active=True).first()
    business_name = business.business_name if business else "Your Local Tradesperson"
    business_phone = business.phone_display if business else "Call Us"

    context = {
        "booking": booking,
        "business_name": business_name,
        "business_phone": business_phone,
        "service": booking.get_service_display(),
    }
    subject = f"Booking enquiry received — {business_name}"
    text_body = render_to_string("trades/emails/booking_confirmation.txt", context)
    html_body = render_to_string("trades/emails/booking_confirmation.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send booking confirmation for enquiry %s.", booking.pk)


def _send_whatsapp_notification(request, booking):
    business = BusinessProfile.objects.filter(is_active=True).first()
    if not business:
        return
    to_number = business.whatsapp_number
    if not to_number:
        return
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_NUMBER

    if not (account_sid and auth_token and from_number):
        logger.warning("WhatsApp notification skipped: Twilio credentials not configured.")
        return

    try:
        client = TwilioClient(account_sid, auth_token)
        service = booking.get_service_display()
        client.messages.create(
            body=f"New booking enquiry from {booking.full_name}\nService: {service}\nPhone: {booking.phone}\nEmail: {booking.email}\nPostcode: {booking.postcode}",
            from_=f'whatsapp:{from_number}',
            to=f'whatsapp:{to_number}',
        )
        logger.info("WhatsApp notification sent for booking %s.", booking.pk)
    except Exception:
        logger.exception("Failed to send WhatsApp notification for enquiry %s.", booking.pk)

# Create your views here.
