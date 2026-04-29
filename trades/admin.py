from django.contrib import admin

from .models import (
    BookingEnquiry,
    BusinessProfile,
    ServiceOffering,
    Testimonial,
    TrustIndicator,
)


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
        "created_at",
    )
    list_filter = ("status", "service", "timeslot", "is_emergency", "preferred_date")
    search_fields = ("full_name", "phone", "email", "postcode", "address")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
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

# Register your models here.
