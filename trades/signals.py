from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import BookingEnquiry, TimeSlotAvailability


def _update_slot_count(business, date, timeslot, delta):
    """Upsert a TimeSlotAvailability row and adjust booked_count."""
    from django.db import transaction

    slot, _ = TimeSlotAvailability.objects.get_or_create(
        business=business,
        date=date,
        timeslot=timeslot,
        defaults={"capacity": business.default_slot_capacity},
    )
    slot.booked_count = max(0, slot.booked_count + delta)
    slot.save(update_fields=["booked_count"])


def _should_count(status):
    """Only count bookings that are not cancelled."""
    return status not in ("cancelled", "canclled")  # note: model uses "cancelled"


@receiver(post_save, sender=BookingEnquiry)
def booking_enquiry_saved(sender, instance, created, **kwargs):
    if instance.business_id is None:
        return
    _update_slot_count(instance.business, instance.preferred_date, instance.timeslot, 1 if _should_count(instance.status) else 0)


@receiver(post_delete, sender=BookingEnquiry)
def booking_enquiry_deleted(sender, instance, **kwargs):
    if instance.business_id is None:
        return
    _update_slot_count(instance.business, instance.preferred_date, instance.timeslot, -1 if _should_count(instance.status) else 0)
