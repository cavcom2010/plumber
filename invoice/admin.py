from django.contrib import admin
from django.utils.html import format_html

from .models import Invoice, InvoiceImage, InvoiceProduct


class InvoiceImageInline(admin.TabularInline):
    model = InvoiceImage
    extra = 0
    readonly_fields = ("image_preview",)
    fields = ("image_preview", "image", "image_type", "sort_order", "caption")

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:100px;border-radius:6px;border:1px solid #e5e7eb;" alt="{}">',
                obj.image.url,
                obj.get_image_type_display(),
            )
        return "—"

    image_preview.short_description = "Preview"


class InvoiceProductInline(admin.TabularInline):
    model = InvoiceProduct
    extra = 0
    fields = ("product_name", "serial_number", "unit_price", "quantity", "warranty_info")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "client_name",
        "service_type",
        "status",
        "total_cost",
        "created_at",
    )
    list_filter = ("status", "service_type")
    search_fields = (
        "invoice_number",
        "client_name",
        "client_phone",
        "client_postcode",
    )
    inlines = (InvoiceImageInline, InvoiceProductInline)
    readonly_fields = ("invoice_number", "total_cost", "created_at", "updated_at")
    fieldsets = (
        (
            "Client",
            {
                "fields": (
                    "client_name",
                    "client_phone",
                    "client_email",
                    "client_address",
                    "client_postcode",
                )
            },
        ),
        (
            "Job",
            {
                "fields": (
                    "service_type",
                    "job_description",
                    "booking_enquiry",
                    "business",
                )
            },
        ),
        (
            "Costs",
            {
                "fields": (
                    "labour_description",
                    "labour_cost",
                    "materials_description",
                    "materials_cost",
                    "total_cost",
                )
            },
        ),
        (
            "Status",
            {"fields": ("status", "notes")},
        ),
        (
            "Timestamps",
            {"fields": ("invoice_number", "created_at", "updated_at")},
        ),
    )
