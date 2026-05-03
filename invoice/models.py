from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models


class Invoice(models.Model):
    class ServiceType(models.TextChoices):
        LEAKING_PIPE = "leaking_pipe", "Leaking Pipe"
        BLOCKED_DRAIN = "blocked_drain", "Blocked Drain"
        WATER_HEATER = "water_heater", "Water Heater"
        TOILET_REPAIR = "toilet_repair", "Toilet Repair"
        BURST_PIPE = "burst_pipe", "Burst Pipe"
        BATHROOM_KITCHEN = "bathroom_kitchen", "Bathroom / Kitchen"
        GAS_PLUMBING = "gas_plumbing", "Gas Plumbing"
        GENERAL = "general", "General Maintenance"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        SENT = "sent", "Sent"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    client_name = models.CharField(max_length=120)
    client_phone = models.CharField(max_length=32)
    client_email = models.EmailField(blank=True)
    client_address = models.CharField(max_length=255)
    client_postcode = models.CharField(max_length=16)
    service_type = models.CharField(max_length=32, choices=ServiceType.choices)
    job_description = models.TextField()
    labour_description = models.TextField(blank=True)
    labour_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    materials_description = models.TextField(blank=True)
    materials_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT
    )
    booking_enquiry = models.ForeignKey(
        "trades.BookingEnquiry",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices",
    )
    business = models.ForeignKey(
        "trades.BusinessProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "invoice"
        verbose_name_plural = "invoices"

    def __str__(self):
        return f"{self.invoice_number or 'Draft'} — {self.client_name}"

    def save(self, *args, **kwargs):
        if self.invoice_number:
            return super().save(*args, **kwargs)

        last_error = None
        for _ in range(5):
            self.invoice_number = self._next_invoice_number()
            try:
                return super().save(*args, **kwargs)
            except IntegrityError as exc:
                last_error = exc
                self.invoice_number = ""
        raise last_error

    @classmethod
    def _next_invoice_number(cls):
        today = date.today()
        prefix = f"INV-{today.year}-"
        last = (
            cls.objects.filter(invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .first()
        )
        next_num = 1
        if last:
            try:
                next_num = int(last.invoice_number.rsplit("-", 1)[-1]) + 1
            except (ValueError, IndexError):
                pass
        return f"{prefix}{next_num:04d}"

    @property
    def total_cost(self):
        labour = Decimal(str(self.labour_cost or 0))
        materials = Decimal(str(self.materials_cost or 0))
        product_total = sum(
            Decimal(str(p.unit_price or 0)) * (p.quantity or 1)
            for p in self.products.all()
        )
        return labour + materials + Decimal(str(product_total))


class InvoiceImage(models.Model):
    class ImageType(models.TextChoices):
        BEFORE = "before", "Before"
        AFTER = "after", "After"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="invoice/images/")
    image_type = models.CharField(max_length=8, choices=ImageType.choices)
    sort_order = models.PositiveSmallIntegerField(default=0)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["image_type", "sort_order"]
        verbose_name = "invoice image"
        verbose_name_plural = "invoice images"

    def __str__(self):
        return f"{self.get_image_type_display()} #{self.sort_order}"

    def clean(self):
        super().clean()
        if self.pk is None:
            count = self.invoice.images.filter(
                image_type=self.image_type
            ).count()
        else:
            count = (
                self.invoice.images.filter(image_type=self.image_type)
                .exclude(pk=self.pk)
                .count()
            )
        if count >= 3:
            raise ValidationError(
                f"Maximum 3 {self.image_type} images per invoice."
            )


class InvoiceProduct(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="products"
    )
    product_name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=200, blank=True)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    warranty_info = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "invoice product"
        verbose_name_plural = "invoice products"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def line_total(self):
        return (self.unit_price or 0) * (self.quantity or 1)
