from django.urls import path

from . import views

urlpatterns = [
    path("", views.trades_home, name="trades_home"),
    path("services/", views.trades_services, name="trades_services"),
    path("about/", views.trades_about, name="trades_about"),
    path("book/", views.trades_booking, name="trades_booking"),
    path("reviews/", views.trades_reviews, name="trades_reviews"),
]
