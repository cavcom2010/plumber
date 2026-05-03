from django import template

register = template.Library()

_SERVICE_ICON_MAP = {
    "leaking_pipe": "icon-droplet",
    "blocked_drain": "icon-droplet",
    "water_heater": "icon-flame",
    "toilet_repair": "icon-wrench",
    "burst_pipe": "icon-alert",
    "bathroom_kitchen": "icon-home",
    "gas_plumbing": "icon-flame",
    "general": "icon-wrench",
    "other": "icon-wrench",
}


@register.simple_tag
def service_icon(service_key):
    icon = _SERVICE_ICON_MAP.get(service_key, "icon-wrench")
    return f"#{icon}"
