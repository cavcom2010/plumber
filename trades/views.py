import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from .forms import BookingEnquiryForm
from .models import BusinessProfile

logger = logging.getLogger(__name__)


def _site_context(extra=None):
    business = (
        BusinessProfile.objects.filter(is_active=True)
        .prefetch_related("trust_indicators", "service_offerings", "testimonials")
        .first()
    )
    context = {
        "business": business,
        "trust_indicators": [],
        "service_offerings": [],
        "testimonials": [],
    }
    if business:
        context.update(
            {
                "trust_indicators": business.trust_indicators.filter(is_active=True),
                "service_offerings": business.service_offerings.filter(is_active=True),
                "testimonials": business.testimonials.filter(is_active=True),
            }
        )
    if extra:
        context.update(extra)
    return context


def trades_home(request):
    return render(request, "trades/home.html", _site_context())


def trades_services(request):
    return render(request, "trades/services.html", _site_context())


def trades_about(request):
    return render(request, "trades/about.html", _site_context())


def trades_reviews(request):
    return render(request, "trades/reviews.html", _site_context())


def trades_booking(request):
    if request.method == "POST":
        form = BookingEnquiryForm(request.POST)
        if form.is_valid():
            booking = form.save()
            _send_booking_notification(request, booking)
            messages.success(
                request,
                "Booking enquiry received. We will call back to confirm availability.",
            )
            return redirect("trades_booking")
    else:
        form = BookingEnquiryForm()

    return render(request, "trades/booking.html", _site_context({"form": form}))


def _send_booking_notification(request, booking):
    recipient = settings.ADMIN_NOTIFICATION_EMAIL
    if not recipient:
        logger.warning("ADMIN_NOTIFICATION_EMAIL is not configured; booking email skipped.")
        return

    context = _site_context({"booking": booking, "request": request})
    subject = (
        f"New plumbing booking enquiry: "
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

# Create your views here.
