from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BusinessProfile, LegalPage, ServiceOffering


class SiteSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return [
            "trades_home",
            "trades_services",
            "trades_about",
            "trades_booking",
            "trades_reviews",
        ]

    def location(self, item):
        return reverse(item)


class ServiceDetailSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7
    protocol = "https"

    def items(self):
        business = BusinessProfile.objects.filter(is_active=True).first()
        if not business:
            return []
        return business.service_offerings.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, "updated_at") else None


class LegalPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.3
    protocol = "https"

    def items(self):
        business = BusinessProfile.objects.filter(is_active=True).first()
        if not business:
            return []
        return business.legal_pages.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, "updated_at") else None
