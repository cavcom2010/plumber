from django.contrib import admin

from .models import BookingEnquiry


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
