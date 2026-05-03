from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    BookingEnquiry,
    BookingImage,
    BusinessProfile,
    ServiceOffering,
    Testimonial,
    TrustIndicator,
)
from .views import testimonial_token_for_booking


class TrustIndicatorInline(admin.TabularInline):
    model = TrustIndicator
    extra = 1
    fields = ("label", "sort_order", "is_active")


class ServiceOfferingInline(admin.TabularInline):
    model = ServiceOffering
    extra = 1
    fields = ("title", "description", "icon", "sort_order", "is_active")


class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 1
    fields = ("quote", "author_name", "author_label", "rating", "sort_order", "is_active")


class BookingImageInline(admin.TabularInline):
    model = BookingImage
    extra = 0
    readonly_fields = ("image_preview", "created_at")
    fields = ("image_preview", "image", "sort_order")

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:100px;border-radius:6px;border:1px solid #e5e7eb;" alt="Diagnostic photo">',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Preview"


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "author_name",
        "business",
        "rating",
        "job_label",
        "author_label",
        "source_booking",
        "is_active",
        "created_at",
    )
    list_filter = ("business", "rating", "is_active", "author_label")
    search_fields = ("author_name", "quote", "job_label", "source_booking__full_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "phone_display", "email", "service_area", "is_active")
    list_filter = ("is_active",)
    search_fields = ("business_name", "phone_display", "email", "service_area")
    inlines = (TrustIndicatorInline, ServiceOfferingInline, TestimonialInline)
    fieldsets = (
        (
            "Brand",
            {
                "fields": (
                    "business_name",
                    "brand_first",
                    "brand_second",
                    "tagline",
                    "meta_description",
                    "is_active",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "phone_display",
                    "phone_href",
                    "whatsapp_number",
                    "whatsapp_prefilled_message",
                    "email",
                    "service_area",
                )
            },
        ),
        (
            "Hero",
            {
                "fields": (
                    "hero_badge",
                    "hero_heading_line_one",
                    "hero_heading_line_two",
                    "hero_body",
                    "hero_image",
                )
            },
        ),
        (
            "Section Copy",
            {
                "fields": (
                    "services_label",
                    "services_title",
                    "services_subtitle",
                    "booking_label",
                    "booking_title",
                    "booking_subtitle",
                    "reviews_label",
                    "reviews_title",
                    "reviews_subtitle",
                )
            },
        ),
        (
            "About",
            {
                "fields": (
                    "about_label",
                    "owner_name",
                    "owner_role",
                    "about_text",
                    "about_image",
                )
            },
        ),
        (
            "Images & Footer",
            {
                "fields": (
                    "services_image",
                    "booking_image",
                    "footer_disclaimer",
                )
            },
        ),
    )


@admin.register(BookingEnquiry)
class BookingEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "email",
        "preferred_date",
        "timeslot",
        "service",
        "postcode",
        "is_emergency",
        "status",
        "testimonial_job_label",
        "testimonial_request_link",
        "create_invoice_link",
        "created_at",
    )
    list_filter = ("status", "service", "timeslot", "is_emergency", "preferred_date")
    search_fields = ("full_name", "phone", "email", "postcode", "address")
    readonly_fields = ("testimonial_request_link", "created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = (BookingImageInline,)
    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    "full_name",
                    "phone",
                    "email",
                    "address",
                    "postcode",
                )
            },
        ),
        (
            "Booking",
            {
                "fields": (
                    "preferred_date",
                    "timeslot",
                    "service",
                    "description",
                    "testimonial_job_label",
                    "is_emergency",
                )
            },
        ),
        (
            "Workflow",
            {
                "fields": (
                    "status",
                    "contacted_at",
                    "admin_notes",
                    "testimonial_request_link",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def testimonial_request_link(self, obj):
        if not obj or not obj.pk:
            return "Save this enquiry before generating a testimonial link."
        token = testimonial_token_for_booking(obj)
        path = reverse("testimonial_put", kwargs={"token": token})
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', path, path)

    testimonial_request_link.short_description = "testimonial link for invoice email"

    def create_invoice_link(self, obj):
        if not obj or not obj.pk:
            return "Save first."
        url = reverse("invoice_create") + f"?booking={obj.pk}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Create Invoice</a>', url
        )

    create_invoice_link.short_description = "create invoice"

# Register your models here.
