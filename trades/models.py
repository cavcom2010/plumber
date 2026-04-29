from django.db import models


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

# Create your models here.
