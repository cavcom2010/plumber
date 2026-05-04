import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from decouple import config
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from trades.models import ServiceOffering


SERVICE_DETAILS = {
    "Leak Repairs": {
        "heading": "Leak Repairs With Clear Fault-Finding",
        "query": "plumber fixing leak pipe repair",
        "body": """Small leaks can quickly become damaged flooring, stained ceilings, or hidden damp. This service is for taps, pipework, under-sink leaks, radiator pipe leaks, waste leaks, and visible water damage where the source needs tracing properly.

The visit focuses on finding the cause, explaining the repair options, and carrying out a tidy fix where parts and access allow. If the leak needs a larger follow-up repair, you will get clear next steps before any extra work is agreed.

Use the booking form to describe where the water is showing, when it started, and whether you can isolate the supply. Photos are especially useful for leak repairs.""",
    },
    "Shower & Bath": {
        "heading": "Shower and Bath Repairs, Replacements, and Upgrades",
        "query": "bathroom shower installation plumber",
        "body": """This service covers leaking showers, loose bath fittings, poor flow, waste problems, resealing, mixer replacements, shower screen issues, and planned upgrades to bath or shower fixtures.

The aim is to leave the bathroom watertight, practical, and cleanly finished. For replacement work, the existing fittings and pipe access are checked first so the right parts can be sourced and avoidable disruption is kept down.

When booking, include the shower or bath type, any visible brand names, and whether the issue is a leak, flow problem, drainage problem, or upgrade request.""",
    },
    "Toilet Repair": {
        "heading": "Toilet Repairs for Flushes, Cisterns, Leaks, and Fittings",
        "query": "toilet repair plumber bathroom",
        "body": """Toilet faults are usually urgent because they affect daily use of the home. This service covers running cisterns, weak or failed flushes, leaks around the pan or inlet, broken seats and fittings, loose toilets, overflow problems, and replacement parts.

The visit starts with a simple diagnosis of the cistern, flush mechanism, inlet valve, waste connection, and visible seals. Straightforward parts can often be replaced during the visit, and anything more involved will be explained clearly before work continues.

For the fastest response, include the toilet style, what has stopped working, and whether water is leaking onto the floor or constantly running into the pan.""",
    },
    "Drain Unblocking": {
        "heading": "Drain Unblocking for Sinks, Baths, Showers, and External Drains",
        "query": "sink drain plumbing",
        "preferred_pixabay_id": 1551390,
        "body": """Blocked drains can cause slow water, smells, overflowing waste, and repeated backups. This service covers blocked sinks, baths, showers, kitchen waste pipes, external gullies, and general drainage issues around the property.

The blockage is assessed before work starts so the right method is used and the likely cause can be explained. The goal is to clear the immediate problem and advise on any signs that point to a recurring fault or damaged pipework.

When booking, say which fixtures are affected, whether more than one drain is slow, and whether the problem is inside, outside, or both.""",
    },
    "Water Heaters": {
        "heading": "Water Heater Checks, Repairs, and Replacement Advice",
        "query": "boiler plumber",
        "preferred_pixabay_id": 4607911,
        "body": """This service is for water heater issues such as no hot water, inconsistent temperature, visible leaks, unusual noises, pressure problems, and general replacement advice.

The visit checks the visible installation, pipework, valves, controls, and symptoms so the fault can be narrowed down safely. Where specialist certification or manufacturer support is required, you will be told clearly and pointed toward the correct next step.

When booking, include the heater type if known, its approximate age, what has changed, and whether there is any visible leaking or loss of pressure.""",
    },
    "Bathroom Fitting": {
        "heading": "Bathroom Fitting and Planned Plumbing Upgrades",
        "query": "bathroom remodel",
        "preferred_pixabay_id": 4130000,
        "body": """This service is for planned bathroom fitting work, fixture changes, pipe alterations, waste connections, taps, showers, baths, basins, toilets, and practical plumbing support during a refresh or refit.

The work is planned around the existing layout, access, water supply, waste routes, and finish you want to achieve. Clear sequencing matters on bathroom projects, so the visit is used to understand the scope and confirm what can be completed in one visit or what needs staged work.

When booking, describe whether this is a small fixture change, a partial upgrade, or a larger bathroom project. Photos of the current bathroom and any chosen fittings help prepare an accurate next step.""",
    },
}


class Command(BaseCommand):
    help = "Prefill active service detail pages and optional Pixabay images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing detail text and images.",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Only update text fields; do not call Pixabay or download images.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        skip_images = options["skip_images"]
        api_key = config("PIXABAY_API_KEY", default="").strip()
        if not skip_images and not api_key:
            raise CommandError("PIXABAY_API_KEY is required unless --skip-images is used.")

        services = ServiceOffering.objects.filter(business__is_active=True).order_by(
            "sort_order", "title"
        )
        updated = 0
        for service in services:
            detail = SERVICE_DETAILS.get(service.title)
            if not detail:
                self.stdout.write(f"Skipped {service.title}: no canned detail content.")
                continue

            if overwrite or not service.detail_heading:
                service.detail_heading = detail["heading"]
            if overwrite or not service.detail_body:
                service.detail_body = detail["body"]

            if not skip_images and (overwrite or not service.detail_image):
                self._set_pixabay_image(service, detail, api_key)

            service.save()
            updated += 1
            self.stdout.write(f"Prefilled {service.title}: {service.get_absolute_url()}")

        self.stdout.write(self.style.SUCCESS(f"Prefilled {updated} service detail pages."))

    def _set_pixabay_image(self, service, detail, api_key):
        params = urlencode(
            {
                "key": api_key,
                "q": detail["query"],
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": 10,
            }
        )
        headers = {"User-Agent": "FlowPro service detail prefill"}
        with urlopen(Request(f"https://pixabay.com/api/?{params}", headers=headers), timeout=20) as response:
            hits = json.load(response).get("hits") or []
        if not hits:
            raise CommandError(f"No Pixabay images found for {service.title}.")

        preferred_id = detail.get("preferred_pixabay_id")
        hit = next((item for item in hits if item.get("id") == preferred_id), hits[0])
        image_url = hit.get("webformatURL") or hit.get("largeImageURL")
        if not image_url:
            raise CommandError(f"No usable Pixabay image URL for {service.title}.")

        time.sleep(2)
        with urlopen(Request(image_url, headers=headers), timeout=30) as image_response:
            content_type = image_response.headers.get("Content-Type", "")
            image_bytes = image_response.read()

        suffix = ".jpg"
        if "png" in content_type:
            suffix = ".png"
        elif "webp" in content_type:
            suffix = ".webp"

        if service.detail_image:
            service.detail_image.delete(save=False)
        filename = f"{service.slug}-pixabay-{hit.get('id', 'image')}{suffix}"
        service.detail_image.save(filename, ContentFile(image_bytes), save=False)
