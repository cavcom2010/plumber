from django.db import migrations, models
from django.utils.text import slugify


def populate_service_slugs(apps, schema_editor):
    ServiceOffering = apps.get_model("trades", "ServiceOffering")

    for service in ServiceOffering.objects.order_by("business_id", "sort_order", "id"):
        base_slug = slugify(service.title)[:90] or "service"
        slug = base_slug
        suffix = 2
        while ServiceOffering.objects.filter(
            business_id=service.business_id,
            slug=slug,
        ).exclude(pk=service.pk).exists():
            suffix_text = f"-{suffix}"
            slug = f"{base_slug[:100 - len(suffix_text)]}{suffix_text}"
            suffix += 1

        service.slug = slug
        if not service.detail_heading:
            service.detail_heading = service.title
        if not service.detail_body:
            service.detail_body = (
                f"{service.description}\n\n"
                "Use this admin-managed page to explain the service, typical "
                "job types, response process, and booking expectations for "
                "this trade."
            )
        service.save(update_fields=["slug", "detail_heading", "detail_body"])


def clear_service_detail_fields(apps, schema_editor):
    ServiceOffering = apps.get_model("trades", "ServiceOffering")
    ServiceOffering.objects.update(slug="", detail_heading="", detail_body="")


class Migration(migrations.Migration):

    dependencies = [
        ("trades", "0009_update_seeded_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceoffering",
            name="slug",
            field=models.SlugField(
                blank=True,
                default="",
                help_text=(
                    "URL slug for the service detail page. Leave blank to "
                    "generate from the title."
                ),
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="serviceoffering",
            name="detail_heading",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Optional heading for the service detail page. Defaults "
                    "to the service title."
                ),
                max_length=140,
            ),
        ),
        migrations.AddField(
            model_name="serviceoffering",
            name="detail_body",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Admin-managed service explanation shown on the service "
                    "detail page."
                ),
            ),
        ),
        migrations.AddField(
            model_name="serviceoffering",
            name="detail_image",
            field=models.ImageField(
                blank=True, upload_to="business/services/detail/"
            ),
        ),
        migrations.RunPython(populate_service_slugs, clear_service_detail_fields),
        migrations.AddConstraint(
            model_name="serviceoffering",
            constraint=models.UniqueConstraint(
                fields=("business", "slug"),
                name="unique_service_slug_per_business",
            ),
        ),
    ]
