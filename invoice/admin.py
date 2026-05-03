from csv import writer as csv_writer
from io import StringIO
from urllib.parse import quote

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Invoice, InvoiceImage, InvoiceProduct


def export_invoices_csv(modeladmin, request, queryset):
    buf = StringIO()
    w = csv_writer(buf)
    w.writerow(["Invoice #", "Client", "Phone", "Email", "Address", "Postcode",
                 "Service", "Status", "Total", "Created", "Sent"])
    for inv in queryset:
        w.writerow([
            inv.invoice_number,
            inv.client_name,
            inv.client_phone,
            inv.client_email,
            inv.client_address,
            inv.client_postcode,
            inv.get_service_type_display(),
            inv.get_status_display(),
            inv.total_cost,
            inv.created_at.strftime("%Y-%m-%d"),
            inv.sent_at.strftime("%Y-%m-%d") if inv.sent_at else "",
        ])
    response = HttpResponse(buf.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=invoices.csv"
    return response


export_invoices_csv.short_description = "Export selected invoices as CSV"


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
        "map_link",
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
    actions = (export_invoices_csv,)

    def map_link(self, obj):
        if obj and obj.client_address:
            query = quote(f"{obj.client_address}, {obj.client_postcode}")
            url = f"https://www.google.com/maps/search/?api=1&query={query}"
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">View on map</a>', url
            )
        return "—"

    map_link.short_description = "map"
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
