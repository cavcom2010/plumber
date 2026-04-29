import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.core import signing
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .forms import BookingEnquiryForm, TestimonialSubmissionForm
from .models import BookingEnquiry, BusinessProfile, Testimonial

logger = logging.getLogger(__name__)
TESTIMONIAL_LINK_SALT = "trades.testimonial-link"
TESTIMONIAL_LINK_MAX_AGE = 60 * 60 * 24 * 180


def testimonial_token_for_booking(booking):
    return signing.dumps({"booking_id": booking.pk}, salt=TESTIMONIAL_LINK_SALT)


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


def testimonial_put(request, token):
    booking = _booking_from_testimonial_token(token)
    business = BusinessProfile.objects.filter(is_active=True).first()
    existing = getattr(booking, "submitted_testimonial", None)

    if request.method == "POST":
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
