from django.urls import path

from . import views

urlpatterns = [
    path("", views.CreateInvoiceView.as_view(), name="invoice_create"),
    path("<int:pk>/", views.ManageInvoiceView.as_view(), name="invoice_manage"),
]
