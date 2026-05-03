import re

from django import forms
from django.conf import settings
from django.core.validators import FileExtensionValidator, validate_email
from django.utils import timezone

from flowpro.settings import get_service_choices

from .models import BookingEnquiry, Testimonial

MAX_DIAGNOSTIC_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


UK_POSTCODE_RE = re.compile(
    r"^(GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$",
    re.IGNORECASE,
)
UK_PHONE_RE = re.compile(r"^(?:(?:\+44)|0)\d{9,10}$")


class BookingEnquiryForm(forms.ModelForm):
    class Meta:
        model = BookingEnquiry
        fields = [
            "full_name",
            "phone",
            "email",
            "preferred_date",
            "address",
            "postcode",
            "service",
            "timeslot",
            "description",
            "is_emergency",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "id": "name",
                    "placeholder": "John Smith",
                    "autocomplete": "name",
                    "aria-describedby": "name-error",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "id": "phone",
                    "type": "tel",
                    "placeholder": "07123 456789",
                    "autocomplete": "tel",
                    "aria-describedby": "phone-error",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "id": "email",
                    "placeholder": "you@example.com",
                    "autocomplete": "email",
                    "aria-describedby": "email-error",
                }
            ),
            "preferred_date": forms.DateInput(
                attrs={"id": "date", "type": "date", "aria-describedby": "date-error"}
            ),
            "address": forms.TextInput(
                attrs={
                    "id": "address",
                    "placeholder": "House number and street name",
                    "autocomplete": "street-address",
                    "aria-describedby": "address-error",
                }
            ),
            "postcode": forms.TextInput(
                attrs={
                    "id": "postcode",
                    "placeholder": "e.g. M20 1AB",
                    "autocomplete": "postal-code",
                    "aria-describedby": "postcode-error",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "id": "description",
                    "rows": 3,
                    "placeholder": "Tell us what is happening - the more detail, the better we can prepare.",
                    "aria-describedby": "description-error",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].choices = get_service_choices()
        for name, field in self.fields.items():
            if name != "email" and not name.startswith("diagnostic_image_"):
                field.required = True
        self.fields["email"].required = False
        self.fields["is_emergency"].required = False

    def clean_full_name(self):
        value = self.cleaned_data["full_name"].strip()
        if len(value) < 2:
            raise forms.ValidationError("Please enter your full name.")
        if len(value.split()) < 2:
            raise forms.ValidationError("Please enter your first and last name.")
        return " ".join(value.split())

    def clean_phone(self):
        value = self.cleaned_data["phone"].strip()
        if getattr(settings, "COUNTRY", "") != "UK":
            return value
        normalised = re.sub(r"[\s().-]", "", value)
        if normalised.startswith("0044"):
            normalised = "+44" + normalised[4:]
        if not UK_PHONE_RE.match(normalised):
            raise forms.ValidationError("Please enter a valid UK phone number.")
        if normalised.startswith("+44"):
            return "+44 " + normalised[3:]
        return f"{normalised[:5]} {normalised[5:]}"

    def clean_email(self):
        value = self.cleaned_data.get("email", "").strip()
        if value:
            validate_email(value)
        return value

    def clean_preferred_date(self):
        value = self.cleaned_data["preferred_date"]
        if value < timezone.localdate():
            raise forms.ValidationError("Please select a date that is not in the past.")
        return value

    def clean_address(self):
        value = self.cleaned_data["address"].strip()
        if len(value) < 5:
            raise forms.ValidationError("Please enter your full address.")
        return value

    def clean_postcode(self):
        value = re.sub(r"\s+", "", self.cleaned_data["postcode"].strip()).upper()
        if getattr(settings, "COUNTRY", "") == "UK":
            if not UK_POSTCODE_RE.match(value):
                raise forms.ValidationError("Please enter a valid UK postcode.")
            return f"{value[:-3]} {value[-3:]}"
        return value

    def clean_description(self):
        value = self.cleaned_data["description"].strip()
        if len(value) < 10:
            raise forms.ValidationError("Please describe the issue in at least 10 characters.")
        return value

    def _validate_image(self, image, field_name):
        if image:
            if image.size > MAX_DIAGNOSTIC_IMAGE_SIZE:
                raise forms.ValidationError("Image must be under 10 MB.")

    diagnostic_image_1 = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        widget=forms.FileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "capture": "environment",
            "aria-describedby": "diagnostic-help-1",
        }),
    )
    diagnostic_image_2 = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        widget=forms.FileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "capture": "environment",
            "aria-describedby": "diagnostic-help-2",
        }),
    )
    diagnostic_image_3 = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        widget=forms.FileInput(attrs={
            "accept": "image/jpeg,image/png,image/webp",
            "capture": "environment",
            "aria-describedby": "diagnostic-help-3",
        }),
    )

    def clean_diagnostic_image_1(self):
        image = self.cleaned_data.get("diagnostic_image_1")
        self._validate_image(image, "diagnostic_image_1")
        return image

    def clean_diagnostic_image_2(self):
        image = self.cleaned_data.get("diagnostic_image_2")
        self._validate_image(image, "diagnostic_image_2")
        return image

    def clean_diagnostic_image_3(self):
        image = self.cleaned_data.get("diagnostic_image_3")
        self._validate_image(image, "diagnostic_image_3")
        return image


class TestimonialSubmissionForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["author_name", "quote", "rating"]
        widgets = {
            "author_name": forms.TextInput(
                attrs={
                    "id": "testimonial-name",
                    "placeholder": "Your name",
                    "autocomplete": "name",
                }
            ),
            "quote": forms.Textarea(
                attrs={
                    "id": "testimonial-quote",
                    "rows": 4,
                    "placeholder": "Tell us how the visit went.",
                }
            ),
            "rating": forms.Select(
                choices=[(5, "5 stars"), (4, "4 stars"), (3, "3 stars"), (2, "2 stars"), (1, "1 star")],
                attrs={"id": "testimonial-rating"},
            ),
        }

    def clean_author_name(self):
        value = self.cleaned_data["author_name"].strip()
        if len(value) < 2:
            raise forms.ValidationError("Please enter your name.")
        return " ".join(value.split())

    def clean_quote(self):
        value = self.cleaned_data["quote"].strip()
        if len(value) < 20:
            raise forms.ValidationError("Please write at least 20 characters.")
        if len(value) > 800:
            raise forms.ValidationError("Please keep your testimonial under 800 characters.")
        return value

    def clean_rating(self):
        value = self.cleaned_data["rating"]
        if value < 1 or value > 5:
            raise forms.ValidationError("Please choose a rating between 1 and 5 stars.")
        return value
