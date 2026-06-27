from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PILImage

from .forms import BookingEnquiryForm
from .models import (
    BookingEnquiry,
    BookingImage,
    BusinessProfile,
    LegalPage,
    ServiceOffering,
    Testimonial,
    TrustIndicator,
)
from .views import testimonial_token_for_booking
from flowpro.settings import get_service_choices


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


def _make_test_image(name="test.jpg"):
    b = BytesIO()
    img = PILImage.new("RGB", (10, 10), color="red")
    img.save(b, format="JPEG")
    b.seek(0)
    return SimpleUploadedFile(name, b.read(), content_type="image/jpeg")


class TradesLandingTests(TestCase):
    def test_business_profile_builds_whatsapp_url(self):
        business = BusinessProfile(
            whatsapp_number="+44 161 555 0123",
            whatsapp_prefilled_message="Hi FlowPro, I need help with a leak.",
        )

        self.assertEqual(
            business.whatsapp_url,
            "https://wa.me/441615550123?text=Hi%20FlowPro%2C%20I%20need%20help%20with%20a%20leak.",
        )

    def test_business_profile_whatsapp_url_without_message(self):
        business = BusinessProfile(
            whatsapp_number="+44 161 555 0123",
            whatsapp_prefilled_message="",
        )

        self.assertEqual(business.whatsapp_url, "https://wa.me/441615550123")

    def test_business_profile_whatsapp_url_is_blank_without_number(self):
        business = BusinessProfile(whatsapp_prefilled_message="Hello")

        self.assertEqual(business.whatsapp_url, "")

    def test_home_page_loads(self):
        response = self.client.get(reverse("trades_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quality Workmanship")
        self.assertContains(response, "What Do You Need Today?")
        self.assertContains(response, "Book a Visit")
        self.assertContains(response, 'aria-label="Mobile navigation"')

    def test_core_static_assets_are_cache_busted(self):
        response = self.client.get(reverse("trades_home"))
        content = response.content.decode()

        self.assertRegex(content, r"trades/css/landing\.css\?v=\d+")
        self.assertRegex(content, r"trades/js/booking\.js\?v=\d+")

    def test_services_page_loads(self):
        response = self.client.get(reverse("trades_services"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Our Services")

    def test_services_page_links_cards_to_detail_pages(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Trades",
            is_active=True,
        )
        service = ServiceOffering.objects.create(
            business=business,
            title="Kitchen Fitting",
            description="Planned kitchen fitting and finishing.",
            detail_body="Admin-written kitchen fitting detail copy.",
        )

        response = self.client.get(reverse("trades_services"))

        self.assertContains(response, service.get_absolute_url())
        self.assertContains(response, "Learn more")

    def test_service_detail_page_uses_admin_content(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Trades",
            services_label="Specialist Work",
            is_active=True,
        )
        service = ServiceOffering.objects.create(
            business=business,
            title="Garden Rooms",
            description="Insulated outdoor rooms built for year-round use.",
            detail_heading="Garden Rooms Built Around the Property",
            detail_body="Admin-managed detail copy for this exact service.",
        )

        response = self.client.get(service.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Garden Rooms Built Around the Property")
        self.assertContains(response, "Admin-managed detail copy for this exact service.")
        self.assertContains(response, "Specialist Work")

    def test_service_detail_only_uses_active_business_services(self):
        BusinessProfile.objects.update(is_active=False)
        inactive_business = BusinessProfile.objects.create(
            business_name="Old Business",
            is_active=False,
        )
        old_service = ServiceOffering.objects.create(
            business=inactive_business,
            title="Old Service",
            slug="shared-service",
            description="Old inactive service.",
            detail_body="This should not be public.",
        )
        active_business = BusinessProfile.objects.create(
            business_name="Current Business",
            is_active=True,
        )
        ServiceOffering.objects.create(
            business=active_business,
            title="Current Service",
            slug="shared-service",
            description="Current active service.",
            detail_body="This is the public service.",
        )

        response = self.client.get(old_service.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This is the public service.")
        self.assertNotContains(response, "This should not be public.")

    def test_inactive_service_detail_returns_404(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Trades",
            is_active=True,
        )
        service = ServiceOffering.objects.create(
            business=business,
            title="Inactive Service",
            description="Hidden service.",
            is_active=False,
        )

        response = self.client.get(service.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_about_page_loads(self):
        response = self.client.get(reverse("trades_about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Meet Your Tradesperson")

    def test_booking_page_loads(self):
        response = self.client.get(reverse("trades_booking"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Service Booking Form")

    def test_reviews_page_loads(self):
        response = self.client.get(reverse("trades_reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What Local Customers Say")

    def test_legal_pages_render_in_footer_and_mobile_menu(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Trades",
            is_active=True,
        )
        page = LegalPage.objects.create(
            business=business,
            title="Privacy Policy",
            slug="privacy-policy",
            summary="How customer details are handled.",
            body="Admin managed privacy content.",
        )

        response = self.client.get(reverse("trades_home"))

        self.assertContains(response, page.get_absolute_url(), count=3)
        self.assertContains(response, "Privacy Policy")
        self.assertContains(response, 'id="mobileMenuToggle"')
        self.assertContains(response, 'id="mobileMenuPanel"')

    def test_legal_page_uses_admin_content(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Trades",
            is_active=True,
        )
        page = LegalPage.objects.create(
            business=business,
            title="Cookie Notice",
            slug="cookie-notice",
            summary="Cookie information.",
            body="Admin managed cookie content.",
        )

        response = self.client.get(page.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cookie Notice")
        self.assertContains(response, "Admin managed cookie content.")

    def test_legal_page_only_uses_active_business_pages(self):
        BusinessProfile.objects.update(is_active=False)
        inactive_business = BusinessProfile.objects.create(
            business_name="Old Business",
            is_active=False,
        )
        old_page = LegalPage.objects.create(
            business=inactive_business,
            title="Privacy Policy",
            slug="privacy-policy",
            body="Old inactive business legal content.",
        )
        active_business = BusinessProfile.objects.create(
            business_name="Current Business",
            is_active=True,
        )
        LegalPage.objects.create(
            business=active_business,
            title="Privacy Policy",
            slug="privacy-policy",
            body="Current active business legal content.",
        )

        response = self.client.get(old_page.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current active business legal content.")
        self.assertNotContains(response, "Old inactive business legal content.")

    def test_inactive_legal_page_returns_404(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Trades",
            is_active=True,
        )
        page = LegalPage.objects.create(
            business=business,
            title="Hidden Page",
            slug="hidden-page",
            body="Hidden content.",
            is_active=False,
        )

        response = self.client.get(page.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_pages_use_active_business_profile_content(self):
        BusinessProfile.objects.update(is_active=False)
        business = BusinessProfile.objects.create(
            business_name="Acme Heating",
            brand_first="Acme",
            brand_second="Heat",
            tagline="Quiet, tidy heating and plumbing.",
            hero_heading_line_one="Trusted Heating",
            hero_heading_line_two="For Local Homes",
            phone_display="020 0000 1111",
            phone_href="+442000001111",
            email="hello@acme.example",
            service_area="Serving Bristol",
            owner_name="Alex Morgan",
            services_title="Heating & Plumbing Services",
            reviews_title="Client Feedback",
            is_active=True,
        )
        TrustIndicator.objects.create(business=business, label="Gas Safe Registered")
        ServiceOffering.objects.create(
            business=business,
            title="Boiler Servicing",
            description="Annual servicing and safety checks.",
            icon=ServiceOffering.IconChoices.FLAME,
        )
        Testimonial.objects.create(
            business=business,
            quote="Clear, tidy, and on time.",
            author_name="Pat C.",
        )

        response = self.client.get(reverse("trades_home"))

        self.assertContains(response, "Acme")
        self.assertContains(response, "Trusted Heating")
        self.assertContains(response, "Gas Safe Registered")
        self.assertContains(response, "What Do You Need Today?")

    def test_whatsapp_link_renders_when_active_business_has_number(self):
        BusinessProfile.objects.update(is_active=False)
        BusinessProfile.objects.create(
            business_name="Acme Heating",
            whatsapp_number="+44 161 555 0123",
            whatsapp_prefilled_message="Hi, I need a booking.",
            is_active=True,
        )

        response = self.client.get(reverse("trades_booking"))

        self.assertContains(
            response,
            "https://wa.me/441615550123?text=Hi%2C%20I%20need%20a%20booking.",
        )
        self.assertContains(response, "Chat on WhatsApp")
        self.assertContains(response, "WhatsApp")

    def test_mobile_nav_falls_back_to_call_without_whatsapp_number(self):
        BusinessProfile.objects.update(whatsapp_number="")

        response = self.client.get(reverse("trades_home"))

        self.assertContains(response, "mobile-nav-call")
        self.assertNotContains(response, "mobile-nav-whatsapp")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ADMIN_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    def test_booking_confirmation_sent_to_client(self):
        response = self.client.post(
            reverse("trades_booking"),
            {
                **valid_booking_data(email="john@example.com"),
                "diagnostic_image_1": "",
                "diagnostic_image_2": "",
                "diagnostic_image_3": "",
            },
        )
        self.assertRedirects(response, reverse("trades_booking"))
        self.assertEqual(len(mail.outbox), 2)
        client_mail = [m for m in mail.outbox if m.to == ["john@example.com"]]
        self.assertEqual(len(client_mail), 1)
        self.assertIn("Booking enquiry received", client_mail[0].subject)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ADMIN_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    def test_valid_booking_creates_enquiry_redirects_and_sends_email(self):
        response = self.client.post(reverse("trades_booking"), valid_booking_data())

        self.assertRedirects(response, reverse("trades_booking"))
        self.assertEqual(BookingEnquiry.objects.count(), 1)
        booking = BookingEnquiry.objects.get()
        self.assertEqual(booking.postcode, "M20 1AB")
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("New booking from Your Local Tradesperson", mail.outbox[0].subject)

    def test_success_redirect_uses_post_redirect_get(self):
        response = self.client.post(reverse("trades_booking"), valid_booking_data())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("trades_booking"))


class BookingEnquiryFormTests(TestCase):
    def test_dynamic_service_choice_values_fit_database_column(self):
        with patch.dict(
            "os.environ",
            {
                "SERVICE_CHOICES": (
                    "Garden Clearance and Waste Removal,"
                    "Garden Clearance and Waste Removal"
                )
            },
        ):
            values = [value for value, label in get_service_choices()]

        self.assertEqual(len(values), 2)
        self.assertEqual(len(set(values)), 2)
        self.assertTrue(all(len(value) <= 32 for value in values))

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

    def test_email_is_optional(self):
        form = BookingEnquiryForm(data=valid_booking_data(email=""))

        self.assertTrue(form.is_valid())


class TestimonialPutTests(TestCase):
    def setUp(self):
        BusinessProfile.objects.update(is_active=False)
        self.business = BusinessProfile.objects.create(
            business_name="FlowPro Plumbing",
            is_active=True,
        )
        self.booking = BookingEnquiry.objects.create(
            full_name="Jane Customer",
            phone="07123 456789",
            email="jane@example.com",
            preferred_date=timezone.localdate(),
            address="10 King Street",
            postcode="M20 1AB",
            service=BookingEnquiry.ServiceChoices.LEAKING_PIPE,
            timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
            description="Kitchen sink repair completed.",
            testimonial_job_label="Kitchen sink repair",
            status=BookingEnquiry.StatusChoices.COMPLETED,
        )
        self.token = testimonial_token_for_booking(self.booking)

    def test_customer_can_open_testimonial_put_endpoint_from_signed_link(self):
        response = self.client.get(reverse("testimonial_put", kwargs={"token": self.token}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leave a Testimonial")
        self.assertContains(response, "Jane Customer")
        self.assertContains(response, "Kitchen sink repair")

    def test_customer_can_submit_testimonial_pending_review(self):
        response = self.client.post(
            reverse("testimonial_put", kwargs={"token": self.token}),
            {
                "author_name": "Jane Customer",
                "rating": "5",
                "quote": "Excellent service, very tidy and clear from start to finish.",
            },
        )

        self.assertRedirects(response, reverse("testimonial_put", kwargs={"token": self.token}))
        testimonial = Testimonial.objects.get(source_booking=self.booking)
        self.assertEqual(testimonial.business, self.business)
        self.assertEqual(testimonial.job_label, "Kitchen sink repair")
        self.assertEqual(testimonial.author_label, "Verified Customer")
        self.assertFalse(testimonial.is_active)

    def test_testimonial_job_label_falls_back_to_booking_service(self):
        self.booking.testimonial_job_label = ""
        self.booking.save(update_fields=["testimonial_job_label"])

        self.client.post(
            reverse("testimonial_put", kwargs={"token": self.token}),
            {
                "author_name": "Jane Customer",
                "rating": "5",
                "quote": "Excellent service, very tidy and clear from start to finish.",
            },
        )

        testimonial = Testimonial.objects.get(source_booking=self.booking)
        self.assertEqual(testimonial.job_label, "Leaking Pipe")

    def test_reviews_page_shows_testimonial_job_label(self):
        Testimonial.objects.create(
            business=self.business,
            source_booking=self.booking,
            author_name="Jane Customer",
            author_label="Verified Customer",
            job_label="Kitchen sink repair",
            quote="Excellent service, very tidy and clear from start to finish.",
            is_active=True,
        )

        response = self.client.get(reverse("trades_reviews"))

        self.assertContains(response, "Kitchen sink repair")

    def test_duplicate_submission_does_not_create_second_testimonial(self):
        Testimonial.objects.create(
            business=self.business,
            source_booking=self.booking,
            author_name="Jane Customer",
            quote="Already submitted testimonial.",
            is_active=False,
        )

        response = self.client.post(
            reverse("testimonial_put", kwargs={"token": self.token}),
            {
                "author_name": "Jane Customer",
                "rating": "5",
                "quote": "Trying to submit this a second time.",
            },
        )

        self.assertRedirects(response, reverse("testimonial_put", kwargs={"token": self.token}))
        self.assertEqual(Testimonial.objects.filter(source_booking=self.booking).count(), 1)

    def test_invalid_testimonial_token_returns_404(self):
        response = self.client.get(reverse("testimonial_put", kwargs={"token": "invalid-token"}))

        self.assertEqual(response.status_code, 404)


class BookingDiagnosticImageTests(TestCase):
    def setUp(self):
        BusinessProfile.objects.update(is_active=False)
        BusinessProfile.objects.create(
            business_name="FlowPro Plumbing",
            is_active=True,
        )

    def test_booking_form_renders_image_upload_fields(self):
        response = self.client.get(reverse("trades_booking"))
        self.assertContains(response, "diagnostic_image_1")
        self.assertContains(response, "Photos of the Issue")
        self.assertContains(response, "image-preview")
        self.assertContains(response, "wizardProgress")
        self.assertContains(response, "bookingSummaryContent")
        self.assertContains(response, "bookingLookupDropdown")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ADMIN_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    def test_booking_with_diagnostic_images_creates_booking_images(self):
        response = self.client.post(
            reverse("trades_booking"),
            {
                **valid_booking_data(),
                "diagnostic_image_1": _make_test_image("leak1.jpg"),
                "diagnostic_image_2": _make_test_image("leak2.jpg"),
            },
        )
        self.assertRedirects(response, reverse("trades_booking"))
        booking = BookingEnquiry.objects.get()
        images = booking.diagnostic_images.all()
        self.assertEqual(images.count(), 2)
        self.assertEqual(images[0].sort_order, 0)
        self.assertEqual(images[1].sort_order, 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ADMIN_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    def test_booking_without_diagnostic_images_works(self):
        response = self.client.post(
            reverse("trades_booking"),
            {
                **valid_booking_data(),
                "diagnostic_image_1": "",
                "diagnostic_image_2": "",
                "diagnostic_image_3": "",
            },
        )
        self.assertRedirects(response, reverse("trades_booking"))
        booking = BookingEnquiry.objects.get()
        self.assertEqual(booking.diagnostic_images.count(), 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ADMIN_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="website@example.com",
    )
    def test_booking_with_only_one_image(self):
        response = self.client.post(
            reverse("trades_booking"),
            {**valid_booking_data(), "diagnostic_image_1": _make_test_image("leak.jpg")},
        )
        self.assertRedirects(response, reverse("trades_booking"))
        self.assertEqual(BookingEnquiry.objects.get().diagnostic_images.count(), 1)
