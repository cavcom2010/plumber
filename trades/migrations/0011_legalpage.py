import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


LEGAL_PAGE_DEFAULTS = [
    (
        "Privacy Policy",
        "How enquiry details are collected, used, and protected.",
        """This page explains how customer information submitted through this website is handled.

Booking enquiry details may include name, phone number, email address, property address, postcode, service requested, preferred appointment information, uploaded photos, and any message supplied through the form.

This information is used to respond to enquiries, arrange visits, prepare for requested work, keep reasonable business records, and follow up on completed jobs where appropriate.

Replace this placeholder with the final privacy policy for the business before launch. The final wording should reflect the real business, tools, email provider, analytics use, retention policy, and legal obligations.""",
    ),
    (
        "Terms of Service",
        "Website and booking enquiry terms for customers.",
        """This website allows customers to submit service enquiries. A submitted enquiry is not a confirmed appointment until the business has reviewed the details and confirmed availability directly.

Prices, attendance times, parts availability, and work scope may depend on inspection, access, safety requirements, and the details provided by the customer.

Customers should provide accurate contact, address, and job information so the business can respond properly. Emergency situations involving immediate danger should be handled by calling the appropriate emergency service or utility provider.

Replace this placeholder with the final terms for the business before launch. The final wording should reflect the real service model, payment terms, guarantees, cancellation policy, and customer obligations.""",
    ),
    (
        "Cookie Notice",
        "Information about basic website cookies and similar technologies.",
        """This website may use essential cookies needed for security, form submission, sessions, and normal website operation.

If analytics, advertising pixels, embedded maps, chat widgets, or other third-party tools are added later, this notice should be updated to explain what is used and why.

Replace this placeholder with the final cookie notice for the business before launch. The final wording should match the actual tools enabled on the site.""",
    ),
]


def seed_legal_pages(apps, schema_editor):
    BusinessProfile = apps.get_model("trades", "BusinessProfile")
    LegalPage = apps.get_model("trades", "LegalPage")

    for business in BusinessProfile.objects.all():
        for index, page in enumerate(LEGAL_PAGE_DEFAULTS, start=1):
            title, summary, body = page
            LegalPage.objects.get_or_create(
                business=business,
                slug=slugify(title),
                defaults={
                    "title": title,
                    "summary": summary,
                    "body": body,
                    "show_in_footer": True,
                    "show_in_mobile_menu": True,
                    "sort_order": index,
                    "is_active": True,
                },
            )


def unseed_legal_pages(apps, schema_editor):
    LegalPage = apps.get_model("trades", "LegalPage")
    LegalPage.objects.filter(
        slug__in=[slugify(title) for title, summary, body in LEGAL_PAGE_DEFAULTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("trades", "0010_serviceoffering_detail_pages"),
    ]

    operations = [
        migrations.CreateModel(
            name="LegalPage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=120)),
                (
                    "slug",
                    models.SlugField(
                        blank=True,
                        default="",
                        help_text=(
                            "URL slug for this page. Leave blank to generate "
                            "from the title."
                        ),
                        max_length=100,
                    ),
                ),
                (
                    "summary",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Short description used for metadata and page intro.",
                        max_length=180,
                    ),
                ),
                (
                    "body",
                    models.TextField(
                        help_text=(
                            "Admin-managed page content. Use plain paragraphs; "
                            "line breaks are preserved."
                        )
                    ),
                ),
                ("show_in_footer", models.BooleanField(default=True)),
                ("show_in_mobile_menu", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "business",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="legal_pages",
                        to="trades.businessprofile",
                    ),
                ),
            ],
            options={
                "verbose_name": "legal/custom page",
                "verbose_name_plural": "legal/custom pages",
                "ordering": ["sort_order", "title"],
            },
        ),
        migrations.AddConstraint(
            model_name="legalpage",
            constraint=models.UniqueConstraint(
                fields=("business", "slug"),
                name="unique_legal_page_slug_per_business",
            ),
        ),
        migrations.RunPython(seed_legal_pages, unseed_legal_pages),
    ]
