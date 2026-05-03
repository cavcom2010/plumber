import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from trades.models import BusinessProfile
from trades.views import testimonial_token_for_booking
from invoice.models import Invoice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send testimonial follow-up reminders for invoices sent 7+ days ago with no testimonial yet."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        invoices = Invoice.objects.filter(
            status__in=["sent", "paid"],
            sent_at__lte=cutoff,
            booking_enquiry__isnull=False,
        ).exclude(
            booking_enquiry__submitted_testimonial__isnull=False,
        ).select_related("booking_enquiry")

        business = BusinessProfile.objects.filter(is_active=True).first()
        business_name = business.business_name if business else "FlowPro Plumbing"
        business_phone = business.phone_display if business else "0161 555 0123"

        sent = 0
        for invoice in invoices:
            booking = invoice.booking_enquiry
            if not booking or not booking.email:
                continue

            token = testimonial_token_for_booking(booking)
            testimonial_url = (
                "https://localhost" + reverse("testimonial_put", kwargs={"token": token})
            )

            context = {
                "invoice": invoice,
                "booking": booking,
                "business_name": business_name,
                "business_phone": business_phone,
                "testimonial_url": testimonial_url,
            }
            subject = f"How was your {booking.get_service_display()}? — {business_name}"
            text_body = render_to_string(
                "trades/emails/testimonial_reminder.txt", context
            )

            message = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.email],
            )

            try:
                message.send(fail_silently=False)
                sent += 1
            except Exception:
                logger.exception(
                    "Failed to send testimonial reminder for booking %s.", booking.pk
                )

        self.stdout.write(
            self.style.SUCCESS(f"Sent {sent} testimonial reminder(s).")
        )
