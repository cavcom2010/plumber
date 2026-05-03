from io import BytesIO

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PILImage

from trades.models import BookingEnquiry, BusinessProfile

from .forms import InvoiceCreateForm
from .models import Invoice, InvoiceImage, InvoiceProduct


def _make_image(name="test.jpg"):
    b = BytesIO()
    img = PILImage.new("RGB", (10, 10), color="red")
    img.save(b, format="JPEG")
    b.seek(0)
    return SimpleUploadedFile(name, b.read(), content_type="image/jpeg")


def _manage_post_data(invoice, **overrides):
    data = {
        "client_name": invoice.client_name,
        "client_phone": invoice.client_phone,
        "client_email": invoice.client_email or "jane@example.com",
        "client_address": invoice.client_address,
        "client_postcode": invoice.client_postcode,
        "service_type": invoice.service_type,
        "job_description": invoice.job_description,
        "status": invoice.status,
        "labour_cost": str(invoice.labour_cost or 0),
        "materials_cost": str(invoice.materials_cost or 0),
    }
    data.update(overrides)
    return data


class InvoiceCreateTests(TestCase):
    def test_create_page_loads(self):
        response = self.client.get(reverse("invoice_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Invoice Draft")
        self.assertContains(response, "invReviewOverlay")
        self.assertContains(response, "Review Invoice Draft")

    def test_valid_submission_creates_draft(self):
        BusinessProfile.objects.update(is_active=False)
        BusinessProfile.objects.create(
            business_name="FlowPro Plumbing",
            is_active=True,
        )
        response = self.client.post(
            reverse("invoice_create"),
            {
                "client_name": "Alice Jones",
                "client_phone": "07123 456789",
                "client_email": "alice@example.com",
                "client_address": "20 Acacia Avenue",
                "client_postcode": "M20 1AB",
                "service_type": "leaking_pipe",
                "job_description": "Kitchen tap is dripping heavily.",
            },
        )
        self.assertRedirects(response, reverse("invoice_create"))
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.client_name, "Alice Jones")
        self.assertEqual(invoice.status, "draft")
        self.assertTrue(invoice.invoice_number.startswith("INV-"))
        self.assertIsNotNone(invoice.business)

    def test_invoice_number_auto_increments(self):
        Invoice.objects.create(
            client_name="First", client_phone="07123 456789",
            client_address="1 Test St", client_postcode="M20 1AB",
            service_type="general", job_description="Job one",
        )
        Invoice.objects.create(
            client_name="Second", client_phone="07123 456789",
            client_address="2 Test St", client_postcode="M20 1AB",
            service_type="general", job_description="Job two",
        )
        self.assertEqual(Invoice.objects.count(), 2)
        nums = list(Invoice.objects.values_list("invoice_number", flat=True))
        self.assertNotEqual(nums[0], nums[1])

    def test_client_phone_validation(self):
        form = InvoiceCreateForm(
            data={
                "client_name": "Bob",
                "client_phone": "not-a-phone",
                "client_address": "1 Test St",
                "client_postcode": "M20 1AB",
                "service_type": "general",
                "job_description": "Fix the thing that is broken definitively.",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("client_phone", form.errors)

    def test_client_postcode_validation(self):
        form = InvoiceCreateForm(
            data={
                "client_name": "Bob",
                "client_phone": "07123 456789",
                "client_address": "1 Test St",
                "client_postcode": "not-a-postcode",
                "service_type": "general",
                "job_description": "Fix the thing that is broken definitively.",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("client_postcode", form.errors)

    def test_create_from_booking_prefills_form(self):
        from trades.models import BookingEnquiry
        BusinessProfile.objects.update(is_active=False)
        BusinessProfile.objects.create(
            business_name="FlowPro Plumbing",
            is_active=True,
        )
        booking = BookingEnquiry.objects.create(
            full_name="Alice Jones",
            phone="+44 7123 456789",
            email="alice@example.com",
            preferred_date=timezone.localdate(),
            address="20 Acacia Avenue",
            postcode="M20 1AB",
            service=BookingEnquiry.ServiceChoices.LEAKING_PIPE,
            timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
            description="Kitchen tap is dripping heavily.",
        )
        response = self.client.get(
            reverse("invoice_create") + f"?booking={booking.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Creating invoice from booking")
        self.assertContains(response, "Alice Jones")
        self.assertContains(response, "Kitchen tap is dripping heavily.")
        self.assertContains(response, "M20 1AB")

    def test_create_from_booking_sets_fk_on_save(self):
        from trades.models import BookingEnquiry
        BusinessProfile.objects.update(is_active=False)
        BusinessProfile.objects.create(
            business_name="FlowPro Plumbing",
            is_active=True,
        )
        booking = BookingEnquiry.objects.create(
            full_name="Alice Jones",
            phone="+44 7123 456789",
            email="alice@example.com",
            preferred_date=timezone.localdate(),
            address="20 Acacia Avenue",
            postcode="M20 1AB",
            service=BookingEnquiry.ServiceChoices.LEAKING_PIPE,
            timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
            description="Kitchen tap is dripping heavily.",
        )
        url = reverse("invoice_create") + f"?booking={booking.pk}"
        response = self.client.post(
            url,
            {
                "client_name": "Alice Jones",
                "client_phone": "07123 456789",
                "client_email": "alice@example.com",
                "client_address": "20 Acacia Avenue",
                "client_postcode": "M20 1AB",
                "service_type": "leaking_pipe",
                "job_description": "Kitchen tap is dripping heavily.",
            },
        )
        self.assertRedirects(response, reverse("invoice_create"))
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.booking_enquiry, booking)
        self.assertEqual(invoice.client_name, "Alice Jones")


class InvoiceManageAccessTests(TestCase):
    def setUp(self):
        self.invoice = Invoice.objects.create(
            client_name="Jane Doe",
            client_phone="07123 456789",
            client_email="jane@example.com",
            client_address="10 Downing St",
            client_postcode="SW1A 2AA",
            service_type="general",
            job_description="Fix all the things.",
        )
        self.user = User.objects.create_user("staff", password="pass")
        self.user.is_staff = True
        self.user.save()
        self.url = reverse("invoice_manage", kwargs={"pk": self.invoice.pk})

    def test_anonymous_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access(self):
        self.client.login(username="staff", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.invoice_number)

    def test_staff_can_upload_before_image(self):
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            self.url,
            _manage_post_data(
                self.invoice,
                status="in_progress",
                new_before_image=_make_image("before.jpg"),
            ),
        )
        self.assertRedirects(response, self.url)
        self.assertEqual(self.invoice.images.filter(image_type="before").count(), 1)

    def test_manage_page_has_lookup_dropdown(self):
        self.client.login(username="staff", password="pass")
        response = self.client.get(self.url)
        self.assertContains(response, "invManageLookupDropdown")
        self.assertContains(response, "booking_enquiry_id")

    def test_manage_form_can_link_booking(self):
        from trades.models import BookingEnquiry
        booking = BookingEnquiry.objects.create(
            full_name="Jane Doe",
            phone="07123 456789",
            email="jane@example.com",
            preferred_date=timezone.localdate(),
            address="10 Downing St",
            postcode="SW1A 2AA",
            service=BookingEnquiry.ServiceChoices.GENERAL,
            timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
            description="Fix all the things.",
        )
        self.assertIsNone(self.invoice.booking_enquiry)

        self.client.login(username="staff", password="pass")
        response = self.client.post(
            self.url,
            _manage_post_data(
                self.invoice,
                status="draft",
                booking_enquiry_id=str(booking.pk),
            ),
        )
        self.assertRedirects(response, self.url)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.booking_enquiry, booking)

    def test_before_image_limit_max_3(self):
        self.client.login(username="staff", password="pass")
        for i in range(3):
            InvoiceImage.objects.create(
                invoice=self.invoice,
                image=_make_image(f"before{i}.jpg"),
                image_type="before",
                sort_order=i,
            )
        self.assertEqual(self.invoice.images.filter(image_type="before").count(), 3)

    def test_can_delete_image_via_form(self):
        self.client.login(username="staff", password="pass")
        img = InvoiceImage.objects.create(
            invoice=self.invoice,
            image=_make_image("before.jpg"),
            image_type="before",
            sort_order=0,
        )
        response = self.client.post(
            self.url,
            _manage_post_data(
                self.invoice,
                status="draft",
                **{f"delete_image_{img.id}": "1"},
            ),
        )
        self.assertRedirects(response, self.url)
        self.assertEqual(self.invoice.images.filter(image_type="before").count(), 0)

    def test_can_manage_products(self):
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            self.url,
            _manage_post_data(
                self.invoice,
                status="draft",
                product_id_0="",
                product_name_0="Worcester Bosch Greenstar 8000",
                product_serial_0="WB-2026-001234",
                product_price_0="1850.00",
                product_qty_0="1",
                product_warranty_0="5 years",
            ),
        )
        self.assertRedirects(response, self.url)
        product = self.invoice.products.get()
        self.assertEqual(product.product_name, "Worcester Bosch Greenstar 8000")
        self.assertEqual(product.serial_number, "WB-2026-001234")
        self.assertEqual(float(product.unit_price), 1850.00)

    def test_product_deletion(self):
        self.client.login(username="staff", password="pass")
        product = InvoiceProduct.objects.create(
            invoice=self.invoice,
            product_name="Old Pump",
            serial_number="OP-001",
        )
        response = self.client.post(
            self.url,
            _manage_post_data(
                self.invoice,
                status="draft",
                product_id_0=str(product.id),
                product_name_0=product.product_name,
                product_serial_0=product.serial_number,
                product_price_0=str(product.unit_price),
                product_qty_0=str(product.quantity),
                product_warranty_0="",
                delete_product_0="1",
            ),
        )
        self.assertRedirects(response, self.url)
        self.assertEqual(self.invoice.products.count(), 0)


class InvoiceEmailTests(TestCase):
    def setUp(self):
        BusinessProfile.objects.update(is_active=False)
        self.business = BusinessProfile.objects.create(
            business_name="FlowPro Plumbing",
            phone_display="0161 555 0123",
            email="hello@flowpro.co.uk",
            is_active=True,
        )
        self.invoice = Invoice.objects.create(
            client_name="Jane Doe",
            client_phone="07123 456789",
            client_email="jane@example.com",
            client_address="10 Downing St",
            client_postcode="SW1A 2AA",
            service_type="general",
            job_description="Fix all the things.",
            business=self.business,
        )
        self.user = User.objects.create_user("staff", password="pass")
        self.user.is_staff = True
        self.user.save()
        self.url = reverse("invoice_manage", kwargs={"pk": self.invoice.pk})

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="website@flowpro.co.uk",
    )
    def test_email_sent_when_status_changes_to_sent(self):
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            self.url,
            _manage_post_data(self.invoice, status="sent"),
        )
        self.assertRedirects(response, self.url)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "sent")
        self.assertIsNotNone(self.invoice.sent_at)
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertIn(self.invoice.invoice_number, sent_mail.subject)
        self.assertEqual(sent_mail.to, ["jane@example.com"])
        self.assertIn("Jane Doe", sent_mail.body)
        self.assertEqual(len(sent_mail.attachments), 1)
        attachment_name, attachment_content, attachment_mime = sent_mail.attachments[0]
        self.assertIn(".pdf", attachment_name)
        self.assertEqual(attachment_mime, "application/pdf")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="website@flowpro.co.uk",
    )
    def test_duplicate_send_prevented_on_second_save(self):
        self.client.login(username="staff", password="pass")
        self.client.post(
            self.url,
            _manage_post_data(self.invoice, status="sent"),
        )
        self.invoice.refresh_from_db()
        self.client.post(
            self.url,
            _manage_post_data(self.invoice, status="sent"),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)

    def test_send_fails_when_email_is_blank(self):
        self.invoice.client_email = ""
        self.invoice.save()
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            self.url,
            _manage_post_data(self.invoice, status="sent", client_email=""),
        )
        self.invoice.refresh_from_db()
        self.assertIsNone(self.invoice.sent_at)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="website@flowpro.co.uk",
    )
    def test_email_includes_testimonial_link_when_booking_linked(self):
        booking = BookingEnquiry.objects.create(
            full_name="Jane Doe",
            phone="07123 456789",
            email="jane@example.com",
            preferred_date=timezone.localdate(),
            address="10 Downing St",
            postcode="SW1A 2AA",
            service=BookingEnquiry.ServiceChoices.LEAKING_PIPE,
            timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
            description="Fix all the things.",
            status=BookingEnquiry.StatusChoices.COMPLETED,
        )
        self.invoice.booking_enquiry = booking
        self.invoice.save()

        self.client.login(username="staff", password="pass")
        self.client.post(
            self.url,
            _manage_post_data(self.invoice, status="sent"),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/put/testimonial/", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="website@flowpro.co.uk",
    )
    def test_pdf_generated_with_invoice_data(self):
        self.client.login(username="staff", password="pass")
        InvoiceProduct.objects.create(
            invoice=self.invoice,
            product_name="Boiler",
            serial_number="B-001",
            unit_price=1200.00,
            quantity=1,
        )
        self.client.post(
            self.url,
            _manage_post_data(self.invoice, status="sent"),
        )
        self.assertEqual(len(mail.outbox), 1)
        _, pdf_content, _ = mail.outbox[0].attachments[0]
        self.assertGreater(len(pdf_content), 100)


class InvoiceTotalCostTests(TestCase):
    def test_total_cost_includes_labour_materials_products(self):
        invoice = Invoice.objects.create(
            client_name="Test", client_phone="07123 456789",
            client_address="1 Test St", client_postcode="M20 1AB",
            service_type="general", job_description="Job",
            labour_cost=150.00, materials_cost=75.50,
        )
        InvoiceProduct.objects.create(
            invoice=invoice, product_name="Boiler",
            serial_number="B-001", unit_price=1200.00, quantity=1,
        )
        InvoiceProduct.objects.create(
            invoice=invoice, product_name="Valve",
            serial_number="V-001", unit_price=25.00, quantity=3,
        )
        self.assertEqual(float(invoice.total_cost), 150.00 + 75.50 + 1200.00 + 75.00)

    def test_total_cost_defaults_to_zero(self):
        invoice = Invoice.objects.create(
            client_name="Test", client_phone="07123 456789",
            client_address="1 Test St", client_postcode="M20 1AB",
            service_type="general", job_description="Job",
        )
        self.assertEqual(float(invoice.total_cost), 0)


class BookingLookupTests(TestCase):
    def setUp(self):
        from trades.models import BookingEnquiry
        BookingEnquiry.objects.create(
            full_name="Calvin Mazhindu",
            phone="+44 7747055935",
            email="calvin2411@hotmail.com",
            preferred_date=timezone.localdate(),
            address="32 Hayden Road",
            postcode="NN10 0HX",
            service=BookingEnquiry.ServiceChoices.TOILET_REPAIR,
            timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
            description="Toilet seat broken",
        )
        BookingEnquiry.objects.create(
            full_name="Alice Smith",
            phone="+44 7123 456789",
            email="alice@example.com",
            preferred_date=timezone.localdate(),
            address="20 Acacia Avenue",
            postcode="M20 1AB",
            service=BookingEnquiry.ServiceChoices.LEAKING_PIPE,
            timeslot=BookingEnquiry.TimeSlotChoices.AFTERNOON,
            description="Kitchen tap dripping",
        )
        self.url = reverse("invoice_booking_lookup")

    def test_returns_matches_by_name(self):
        resp = self.client.get(self.url + "?q=mazhindu")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["full_name"], "Calvin Mazhindu")

    def test_returns_matches_by_phone(self):
        resp = self.client.get(self.url + "?q=07747")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["phone"], "+44 7747055935")

    def test_returns_matches_by_email(self):
        resp = self.client.get(self.url + "?q=calvin2411")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["email"], "calvin2411@hotmail.com")

    def test_case_insensitive(self):
        resp = self.client.get(self.url + "?q=CALVIN")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_short_query_returns_empty(self):
        resp = self.client.get(self.url + "?q=a")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_no_match_returns_empty(self):
        resp = self.client.get(self.url + "?q=zzznotfound")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_no_query_returns_empty(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_max_10_results(self):
        from trades.models import BookingEnquiry
        for i in range(15):
            BookingEnquiry.objects.create(
                full_name=f"Test User {i}",
                phone=f"07123 4567{i:02d}",
                preferred_date=timezone.localdate(),
                address="Test St",
                postcode="M20 1AB",
                service=BookingEnquiry.ServiceChoices.GENERAL,
                timeslot=BookingEnquiry.TimeSlotChoices.MORNING,
                description="Job",
            )
        resp = self.client.get(self.url + "?q=Test")
        self.assertEqual(len(resp.json()), 10)

    def test_response_has_all_fields(self):
        resp = self.client.get(self.url + "?q=mazhindu")
        data = resp.json()[0]
        self.assertIn("id", data)
        self.assertIn("full_name", data)
        self.assertIn("phone", data)
        self.assertIn("email", data)
        self.assertIn("address", data)
        self.assertIn("postcode", data)
        self.assertIn("service", data)
        self.assertIn("service_display", data)
        self.assertIn("description", data)
