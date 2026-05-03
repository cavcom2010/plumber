from datetime import date

from django.contrib import admin
from django.db.models import Q
from django.utils import timezone

_original_admin_index = admin.site.index


def _patched_index(self, request, extra_context=None):
    extra_context = extra_context or {}
    today = timezone.localdate()

    from trades.models import BookingEnquiry
    extra_context["new_bookings_today"] = BookingEnquiry.objects.filter(
        created_at__date=today
    ).count()

    month_start = today.replace(day=1)
    from invoice.models import Invoice
    sent_paid = Invoice.objects.filter(
        status__in=["sent", "paid"],
        sent_at__date__gte=month_start,
    )
    extra_context["revenue_this_month"] = sum(
        i.total_cost for i in sent_paid
    )

    from trades.models import Testimonial
    extra_context["pending_testimonials"] = Testimonial.objects.filter(
        is_active=False
    ).count()

    extra_context["unsent_invoices"] = Invoice.objects.filter(
        Q(status="completed") | Q(status="draft") | Q(status="in_progress")
    ).count()

    template_response = _original_admin_index(request, extra_context)
    template_response.template_name = "admin/dashboard.html"
    return template_response


admin.site.index_template = "admin/dashboard.html"
admin.site.index = _patched_index.__get__(admin.site, admin.site.__class__)
