from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import BookingEnquiryForm
from .models import BookingEnquiry


def valid_booking_data(**overrides):
    data = {
        "full_name": "John Smith",
        "phone": "07123 456789",
        "email": "john@example.com",
        "preferred_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
        "address": "10 King Street",
        "postcode": "M20 1AB",
        "service": BookingEnquiry.ServiceChoices.LEAKING_PIPE,
        "timeslot": BookingEnquiry.TimeSlotChoices.MORNING,
        "description": "There is a slow leak under the kitchen sink.",
    }
    data.update(overrides)
    return data


class TradesLandingTests(TestCase):
    def test_landing_page_loads(self):
        response = self.client.get(reverse("trades_landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium Plumbing")
        self.assertContains(response, "Service Booking Form")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ADMIN_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    def test_valid_booking_creates_enquiry_redirects_and_sends_email(self):
        response = self.client.post(reverse("trades_landing"), valid_booking_data())

        self.assertRedirects(response, reverse("trades_landing"))
        self.assertEqual(BookingEnquiry.objects.count(), 1)
        booking = BookingEnquiry.objects.get()
        self.assertEqual(booking.postcode, "M20 1AB")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New plumbing booking enquiry", mail.outbox[0].subject)

    def test_success_redirect_uses_post_redirect_get(self):
        response = self.client.post(reverse("trades_landing"), valid_booking_data())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("trades_landing"))


class BookingEnquiryFormTests(TestCase):
    def test_invalid_date_in_past_is_rejected(self):
        form = BookingEnquiryForm(
            data=valid_booking_data(
                preferred_date=(timezone.localdate() - timedelta(days=1)).isoformat()
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("preferred_date", form.errors)

    def test_invalid_postcode_is_rejected(self):
        form = BookingEnquiryForm(data=valid_booking_data(postcode="not-a-postcode"))

        self.assertFalse(form.is_valid())
        self.assertIn("postcode", form.errors)

    def test_invalid_phone_is_rejected(self):
        form = BookingEnquiryForm(data=valid_booking_data(phone="12345"))

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_optional_email_can_be_blank(self):
        form = BookingEnquiryForm(data=valid_booking_data(email=""))

        self.assertTrue(form.is_valid(), form.errors)

# Create your tests here.
