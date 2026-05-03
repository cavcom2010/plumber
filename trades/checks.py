from django.conf import settings
from django.core.checks import Error, Warning, register


UNSAFE_SECRET_KEYS = {
    "",
    "change-me",
    "change-me-for-local-development-only",
}


@register()
def production_settings_check(app_configs, **kwargs):
    issues = []

    if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
        issues.append(
            Error(
                "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.",
                id="trades.E001",
            )
        )

    if not settings.DEBUG:
        if settings.SECRET_KEY in UNSAFE_SECRET_KEYS:
            issues.append(
                Warning(
                    "SECRET_KEY is still using an unsafe template value.",
                    hint="Set a unique SECRET_KEY in this clone's .env.",
                    id="trades.W001",
                )
            )

        if "*" in settings.ALLOWED_HOSTS:
            issues.append(
                Warning(
                    "ALLOWED_HOSTS contains a wildcard in production mode.",
                    hint="Set explicit hostnames for this clone.",
                    id="trades.W002",
                )
            )

        if settings.EMAIL_BACKEND.endswith(".console.EmailBackend"):
            issues.append(
                Warning(
                    "Email is configured to use the console backend in production mode.",
                    hint="Set EMAIL_PROVIDER and SMTP credentials before launch.",
                    id="trades.W003",
                )
            )

        if not settings.ADMIN_NOTIFICATION_EMAIL:
            issues.append(
                Warning(
                    "ADMIN_NOTIFICATION_EMAIL is empty.",
                    hint="Set the recipient that should receive booking enquiries.",
                    id="trades.W004",
                )
            )

    return issues
