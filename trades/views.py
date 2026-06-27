import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.core import signing
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .decorators import rate_limit
from .forms import BookingEnquiryForm, TestimonialSubmissionForm
from .models import (
    BookingEnquiry,
    BookingImage,
    BusinessProfile,
    LegalPage,
    ServiceOffering,
    Testimonial,
    TimeSlotAvailability,
)
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


@cache_page(60 * 15)
def trades_home(request):
    return render(request, "trades/home.html", _site_context())


@cache_page(60 * 15)
def trades_services(request):
    return render(request, "trades/services.html", _site_context())


@cache_page(60 * 15)
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


@cache_page(60 * 15)
def trades_about(request):
    return render(request, "trades/about.html", _site_context())


@cache_page(60 * 15)
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


@cache_page(60 * 15)
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
            booking = form.save(commit=False)
            booking.business = BusinessProfile.objects.filter(is_active=True).first()
            booking.save()
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

    service = booking.get_service_display()
    emergency = " !!! EMERGENCY !!!" if booking.is_emergency else ""
    body = (
        f"New booking enquiry{emergency}\n"
        f"Name: {booking.full_name}\n"
        f"Service: {service}\n"
        f"Phone: {booking.phone}\n"
        f"Email: {booking.email or 'not provided'}\n"
        f"Address: {booking.address}\n"
        f"Postcode: {booking.postcode}\n"
        f"Date: {booking.preferred_date}\n"
        f"Time: {booking.get_timeslot_display()}\n"
        f"Problem: {booking.description}"
    )

    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    cloud_api_token = settings.WHATSAPP_CLOUD_API_TOKEN

    if phone_number_id and cloud_api_token:
        try:
            import json
            from urllib.request import Request, urlopen
            from urllib.error import URLError

            payload = json.dumps({
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": body},
            }).encode("utf-8")

            req = Request(
                f"https://graph.facebook.com/v22.0/{phone_number_id}/messages",
                data=payload,
                headers={
                    "Authorization": f"Bearer {cloud_api_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            response = urlopen(req, timeout=10)
            response_body = response.read().decode("utf-8")
            response_data = json.loads(response_body)

            if "error" in response_data:
                error_info = response_data["error"]
                logger.error(
                    "WhatsApp Cloud API error for booking %s: %s (code %s)",
                    booking.pk,
                    error_info.get("message", "unknown"),
                    error_info.get("code", "unknown"),
                )
            else:
                message_id = None
                if response_data.get("messages"):
                    message_id = response_data["messages"][0].get("id")
                logger.info(
                    "WhatsApp Cloud API notification sent for booking %s (wa_id=%s)",
                    booking.pk,
                    message_id or "unknown",
                )
            return
        except Exception:
            logger.exception("Failed to send WhatsApp Cloud API notification for enquiry %s.", booking.pk)
            return

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_NUMBER

    if not (account_sid and auth_token and from_number):
        logger.warning("WhatsApp notification skipped: neither Cloud API nor Twilio credentials configured.")
        return

    try:
        from twilio.rest import Client as TwilioClient
        client = TwilioClient(account_sid, auth_token)
        client.messages.create(
            body=body,
            from_=f'whatsapp:{from_number}',
            to=f'whatsapp:{to_number}',
        )
        logger.info("WhatsApp notification sent for booking %s.", booking.pk)
    except Exception:
        logger.exception("Failed to send WhatsApp notification for enquiry %s.", booking.pk)

def api_available_slots(request):
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse({"error": "date parameter required"}, status=400)

    try:
        from datetime import date as date_type
        target_date = date_type.fromisoformat(date_str)
    except (ValueError, TypeError):
        return JsonResponse({"error": "invalid date format"}, status=400)

    business = BusinessProfile.objects.filter(is_active=True).first()
    if not business:
        return JsonResponse({"slots": []})

    all_slots = [choice[0] for choice in BookingEnquiry.TimeSlotChoices.choices]
    blocked_slots = set()
    existing = TimeSlotAvailability.objects.filter(
        business=business,
        date=target_date,
    )
    for slot in existing:
        if not slot.is_available:
            blocked_slots.add(slot.timeslot)

    available = [
        slot for slot in all_slots
        if slot not in blocked_slots
    ]
    return JsonResponse({"slots": available, "date": date_str})
