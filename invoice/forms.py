import re

from django import forms
from django.core.validators import FileExtensionValidator

from .models import Invoice, InvoiceImage, InvoiceProduct

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
UK_POSTCODE_RE = re.compile(
    r"^(GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$",
    re.IGNORECASE,
)
UK_PHONE_RE = re.compile(r"^(?:(?:\+44)|0)\d{9,10}$")


def validate_image_size(image):
    if image.size > MAX_UPLOAD_SIZE:
        raise forms.ValidationError("Image must be under 10 MB.")


class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "client_name",
            "client_phone",
            "client_email",
            "client_address",
            "client_postcode",
            "service_type",
            "job_description",
        ]
        widgets = {
            "client_name": forms.TextInput(
                attrs={
                    "id": "inv-name",
                    "placeholder": "Full name",
                    "autocomplete": "name",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "id": "inv-phone",
                    "type": "tel",
                    "placeholder": "07123 456789",
                    "autocomplete": "tel",
                }
            ),
            "client_email": forms.EmailInput(
                attrs={
                    "id": "inv-email",
                    "placeholder": "you@example.com",
                    "autocomplete": "email",
                }
            ),
            "client_address": forms.TextInput(
                attrs={
                    "id": "inv-address",
                    "placeholder": "House number and street name",
                    "autocomplete": "street-address",
                }
            ),
            "client_postcode": forms.TextInput(
                attrs={
                    "id": "inv-postcode",
                    "placeholder": "e.g. M20 1AB",
                    "autocomplete": "postal-code",
                }
            ),
            "job_description": forms.Textarea(
                attrs={
                    "id": "inv-description",
                    "rows": 3,
                    "placeholder": "Describe the job — the more detail, the better.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in [
            "client_name",
            "client_phone",
            "client_address",
            "client_postcode",
            "service_type",
            "job_description",
        ]:
            self.fields[name].required = True
        self.fields["client_email"].required = False

    def clean_client_name(self):
        value = self.cleaned_data["client_name"].strip()
        if len(value) < 2:
            raise forms.ValidationError("Please enter the client's full name.")
        return " ".join(value.split())

    def clean_client_phone(self):
        value = self.cleaned_data["client_phone"].strip()
        normalised = re.sub(r"[\s().-]", "", value)
        if normalised.startswith("0044"):
            normalised = "+44" + normalised[4:]
        if not UK_PHONE_RE.match(normalised):
            raise forms.ValidationError("Please enter a valid UK phone number.")
        if normalised.startswith("+44"):
            return "+44 " + normalised[3:]
        return f"{normalised[:5]} {normalised[5:]}"

    def clean_client_postcode(self):
        value = re.sub(r"\s+", "", self.cleaned_data["client_postcode"].strip()).upper()
        if not UK_POSTCODE_RE.match(value):
            raise forms.ValidationError("Please enter a valid UK postcode.")
        return f"{value[:-3]} {value[-3:]}"


class InvoiceManageForm(forms.ModelForm):
    new_before_image = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
        widget=forms.FileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "capture": "environment",
                "id": "new-before-image",
            }
        ),
    )
    new_after_image = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
        widget=forms.FileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "capture": "environment",
                "id": "new-after-image",
            }
        ),
    )

    class Meta:
        model = Invoice
        fields = [
            "client_name",
            "client_phone",
            "client_email",
            "client_address",
            "client_postcode",
            "service_type",
            "job_description",
            "labour_description",
            "labour_cost",
            "materials_description",
            "materials_cost",
            "notes",
            "status",
        ]
        widgets = {
            "client_name": forms.TextInput(
                attrs={
                    "id": "inv-name",
                    "placeholder": "Full name",
                    "autocomplete": "name",
                }
            ),
            "client_phone": forms.TextInput(
                attrs={
                    "id": "inv-phone",
                    "type": "tel",
                    "autocomplete": "tel",
                }
            ),
            "client_email": forms.EmailInput(
                attrs={
                    "id": "inv-email",
                    "autocomplete": "email",
                }
            ),
            "client_address": forms.TextInput(
                attrs={
                    "id": "inv-address",
                    "autocomplete": "street-address",
                }
            ),
            "client_postcode": forms.TextInput(
                attrs={
                    "id": "inv-postcode",
                    "autocomplete": "postal-code",
                }
            ),
            "job_description": forms.Textarea(
                attrs={"id": "inv-description", "rows": 3}
            ),
            "labour_description": forms.Textarea(
                attrs={"id": "inv-labour-desc", "rows": 2}
            ),
            "materials_description": forms.Textarea(
                attrs={"id": "inv-materials-desc", "rows": 2}
            ),
            "notes": forms.Textarea(
                attrs={"id": "inv-notes", "rows": 2}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in [
            "client_name",
            "client_phone",
            "client_email",
            "client_address",
            "client_postcode",
            "service_type",
            "job_description",
        ]:
            self.fields[name].required = True
        self.fields["client_email"].required = True

    def clean_client_phone(self):
        value = self.cleaned_data["client_phone"].strip()
        normalised = re.sub(r"[\s().-]", "", value)
        if normalised.startswith("0044"):
            normalised = "+44" + normalised[4:]
        if not UK_PHONE_RE.match(normalised):
            raise forms.ValidationError("Please enter a valid UK phone number.")
        if normalised.startswith("+44"):
            return "+44 " + normalised[3:]
        return f"{normalised[:5]} {normalised[5:]}"

    def clean_client_postcode(self):
        value = re.sub(r"\s+", "", self.cleaned_data["client_postcode"].strip()).upper()
        if not UK_POSTCODE_RE.match(value):
            raise forms.ValidationError("Please enter a valid UK postcode.")
        return f"{value[:-3]} {value[-3:]}"
