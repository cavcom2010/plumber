import os
from functools import lru_cache
from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path):
    url = static(path)
    version = _static_asset_version(path)
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode({'v': version})}"


@lru_cache(maxsize=128)
def _static_asset_version(path):
    found_path = finders.find(path)
    if found_path:
        return str(os.stat(found_path).st_mtime_ns)
    return getattr(settings, "STATIC_ASSET_VERSION", "1")
