from django.urls import path

from . import views

urlpatterns = [
    path("", views.trades_landing, name="trades_landing"),
]
