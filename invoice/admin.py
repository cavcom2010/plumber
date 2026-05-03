from django.contrib import admin

from .models import Invoice, InvoiceImage, InvoiceProduct


class InvoiceImageInline(admin.TabularInline):
    model = InvoiceImage
    extra = 0
    fields = ("image", "image_type", "sort_order", "caption")


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
