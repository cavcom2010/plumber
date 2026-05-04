import logging
import time

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_PERIOD_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_rate(rate_str):
    try:
        count_str, period = rate_str.strip().rsplit("/", 1)
        count = int(count_str)
        if count < 1:
            return 0, 0
        seconds = _PERIOD_SECONDS.get(period)
        if not seconds:
            return 0, 0
        return count, seconds
    except (ValueError, AttributeError):
        return 0, 0


def rate_limit(rate_setting):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            rate_str = getattr(settings, rate_setting, "")
            if not rate_str:
                return view_func(request, *args, **kwargs)

            count, period = _parse_rate(rate_str)
            if not count:
                return view_func(request, *args, **kwargs)

            ip = _client_ip(request)
            view_key = view_func.__name__
            now = int(time.time())
            window_start = now - (now % period)
            cache_key = f"rl:{ip}:{view_key}:{window_start}"

            try:
                current = cache.get(cache_key, 0)
                if current >= count:
                    logger.warning(
                        "Rate limit exceeded for %s on %s (%d/%s)",
                        ip, view_key, count, period,
                    )
                    request._rate_limited = True
            except Exception:
                logger.debug("Cache unavailable for rate limiting; allowing request.")
                return view_func(request, *args, **kwargs)

            try:
                cache.set(cache_key, current + 1, timeout=period + 10)
            except Exception:
                pass

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def _client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
