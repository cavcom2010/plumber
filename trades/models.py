import re
from urllib.parse import quote

from django.db import models


class BusinessProfile(models.Model):
    business_name = models.CharField(max_length=120, default="FlowPro Plumbing")
    brand_first = models.CharField(max_length=40, default="Flow")
    brand_second = models.CharField(max_length=40, default="Pro")
    tagline = models.CharField(
        max_length=180,
        default="Premium local plumbing services - fast, clear, and reliable.",
    )
    meta_description = models.TextField(
        default=(
            "Premium local plumbing services with fast response, online booking, "
            "emergency call-outs, leak repairs, bathroom fitting, and drain unblocking."
        )
    )
    hero_badge = models.CharField(
        max_length=120,
        default="Trusted local plumbing specialists",
    )
    hero_heading_line_one = models.CharField(max_length=80, default="Premium Plumbing")
    hero_heading_line_two = models.CharField(max_length=80, default="Without the Stress")
    hero_body = models.TextField(
        default=(
            "Reliable local plumbers for urgent repairs, leaks, drains, bathrooms, "
            "and general maintenance. Clear communication, tidy workmanship, and "
            "fast call-backs."
        )
    )
    phone_display = models.CharField(max_length=40, default="0161 555 0123")
    phone_href = models.CharField(max_length=40, default="+441615550123")
    whatsapp_number = models.CharField(
        max_length=32,
        blank=True,
        help_text="International WhatsApp number. Use digits or + format, e.g. +441615550123.",
    )
    whatsapp_prefilled_message = models.TextField(
        blank=True,
        default="Hi, I would like to enquire about plumbing services.",
        help_text="Message prefilled when a customer opens WhatsApp chat.",
    )
    email = models.EmailField(default="hello@flowpro-plumbing.co.uk")
    service_area = models.CharField(
        max_length=160,
        default="Serving Manchester & surrounding areas",
    )
    owner_name = models.CharField(max_length=120, default="Mark Henderson")
    owner_role = models.CharField(max_length=120, default="Local Plumbing Specialist")
    about_label = models.CharField(max_length=80, default="Meet Your Plumber")
    about_text = models.TextField(
        default=(
            "FlowPro is built around a simple promise: clear communication, fair "
            "pricing, and respect for your home. This section can be replaced with "
            "the real business owner's story, qualifications, guarantees, and "
            "service area."
        )
    )
    services_label = models.CharField(max_length=80, default="Our Services")
    services_title = models.CharField(
        max_length=120,
        default="Complete Plumbing Solutions",
    )
    services_subtitle = models.TextField(
        default=(
            "A flexible service template for local trades: quick repairs, planned "
            "installs, maintenance visits, and emergency call-outs."
        )
    )
    booking_label = models.CharField(max_length=80, default="Book a Visit")
    booking_title = models.CharField(max_length=120, default="Schedule Your Service")
    booking_subtitle = models.TextField(
        default=(
            "Send a booking enquiry and the team will confirm availability. For "
            "urgent issues, call directly for the fastest response."
        )
    )
    reviews_label = models.CharField(max_length=80, default="Testimonials")
    reviews_title = models.CharField(max_length=120, default="What Local Customers Say")
    reviews_subtitle = models.TextField(
        default="Use this area for real verified customer reviews once the business has approved them."
    )
    footer_disclaimer = models.TextField(
        default=(
            "Replace claims, reviews, insurance details, and qualifications with "
            "verified client information."
        )
    )
    hero_image = models.ImageField(upload_to="business/hero/", blank=True)
    services_image = models.ImageField(upload_to="business/services/", blank=True)
    about_image = models.ImageField(upload_to="business/about/", blank=True)
    booking_image = models.ImageField(upload_to="business/booking/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "business_name"]
        verbose_name = "business profile"
        verbose_name_plural = "business profiles"

    def __str__(self):
        return self.business_name

    @property
    def whatsapp_url(self):
        number = re.sub(r"\D", "", self.whatsapp_number or "")
        if not number:
            return ""

        message = self.whatsapp_prefilled_message.strip()
        if not message:
            return f"https://wa.me/{number}"

        return f"https://wa.me/{number}?text={quote(message)}"


class TrustIndicator(models.Model):
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="trust_indicators",
    )
    label = models.CharField(max_length=80)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "label"]
        verbose_name = "trust indicator"
        verbose_name_plural = "trust indicators"

    def __str__(self):
        return self.label


class ServiceOffering(models.Model):
    class IconChoices(models.TextChoices):
        WRENCH = "icon-wrench", "Wrench"
        SHOWER = "icon-shower", "Shower"
        DROPLET = "icon-droplet", "Droplet"
        FLAME = "icon-flame", "Flame"
        HOME = "icon-home", "Home"

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="service_offerings",
    )
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=160)
    icon = models.CharField(
        max_length=40,
        choices=IconChoices.choices,
        default=IconChoices.WRENCH,
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "service offering"
        verbose_name_plural = "service offerings"

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="testimonials",
    )
    source_booking = models.OneToOneField(
        "BookingEnquiry",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="submitted_testimonial",
    )
    job_label = models.CharField(max_length=140, blank=True)
    quote = models.TextField()
    author_name = models.CharField(max_length=80)
    author_label = models.CharField(max_length=80, default="Local Customer")
    rating = models.PositiveSmallIntegerField(default=5)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "author_name"]
        verbose_name = "testimonial"
        verbose_name_plural = "testimonials"

    def __str__(self):
        return f"{self.author_name} - {self.rating} stars"


class BookingEnquiry(models.Model):
    class ServiceChoices(models.TextChoices):
        LEAKING_PIPE = "leaking_pipe", "Leaking Pipe"
        BLOCKED_DRAIN = "blocked_drain", "Blocked Drain"
        WATER_HEATER = "water_heater", "Water Heater"
        TOILET_REPAIR = "toilet_repair", "Toilet Repair"
        BURST_PIPE = "burst_pipe", "Burst Pipe"
        BATHROOM_KITCHEN = "bathroom_kitchen", "Bathroom / Kitchen"
        GAS_PLUMBING = "gas_plumbing", "Gas Plumbing"
        GENERAL = "general", "General Maintenance"
        OTHER = "other", "Other"

    class TimeSlotChoices(models.TextChoices):
        EARLY = "7am-9am", "7am-9am"
        MORNING = "9am-11am", "9am-11am"
        MIDDAY = "11am-1pm", "11am-1pm"
        AFTERNOON = "1pm-3pm", "1pm-3pm"
        LATE_AFTERNOON = "3pm-5pm", "3pm-5pm"
        EVENING = "5pm-7pm", "5pm-7pm"

    class StatusChoices(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        BOOKED = "booked", "Booked"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    full_name = models.CharField(max_length=120, verbose_name="full name")
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    preferred_date = models.DateField(verbose_name="preferred date")
    address = models.CharField(max_length=255)
    postcode = models.CharField(max_length=16)
    service = models.CharField(max_length=32, choices=ServiceChoices.choices)
    timeslot = models.CharField(
        max_length=16,
        choices=TimeSlotChoices.choices,
        verbose_name="preferred time slot",
    )
    description = models.TextField()
    testimonial_job_label = models.CharField(
        max_length=140,
        blank=True,
        verbose_name="testimonial job label",
        help_text="Customer-facing completed job label shown on review cards, e.g. Bathroom tap repair.",
    )
    is_emergency = models.BooleanField(default=False, verbose_name="emergency")
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )
    admin_notes = models.TextField(blank=True, verbose_name="admin notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contacted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "booking enquiry"
        verbose_name_plural = "booking enquiries"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["preferred_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_emergency"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_service_display()} - {self.postcode}"

    @property
    def testimonial_job_display(self):
        return self.testimonial_job_label.strip() or self.get_service_display()


class BookingImage(models.Model):
    booking = models.ForeignKey(
        BookingEnquiry,
        on_delete=models.CASCADE,
        related_name="diagnostic_images",
    )
    image = models.ImageField(upload_to="booking/diagnostics/")
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "created_at"]
        verbose_name = "booking diagnostic image"
        verbose_name_plural = "booking diagnostic images"

    def __str__(self):
        return f"Image {self.sort_order} for {self.booking}"
