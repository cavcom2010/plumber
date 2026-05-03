from django.urls import path

from . import views

urlpatterns = [
    path("", views.CreateInvoiceView.as_view(), name="invoice_create"),
    path("api/bookings/", views.booking_lookup, name="invoice_booking_lookup"),
    path("<int:pk>/", views.ManageInvoiceView.as_view(), name="invoice_manage"),
]
