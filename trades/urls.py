from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import LegalPageSitemap, ServiceDetailSitemap, SiteSitemap

sitemaps = {
    "pages": SiteSitemap,
    "services": ServiceDetailSitemap,
    "legal": LegalPageSitemap,
}

urlpatterns = [
    path("", views.trades_home, name="trades_home"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("services/", views.trades_services, name="trades_services"),
    path("service/<slug:slug>/", views.trades_service_detail, name="trades_service_detail"),
    path("about/", views.trades_about, name="trades_about"),
    path("book/", views.trades_booking, name="trades_booking"),
    path("reviews/", views.trades_reviews, name="trades_reviews"),
    path("legal/<slug:slug>/", views.trades_legal_page, name="trades_legal_page"),
    path("put/testimonial/<path:token>/", views.testimonial_put, name="testimonial_put"),
]
