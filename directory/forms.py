from django.forms import ModelForm, TextInput, Textarea, EmailInput, DecimalField, NumberInput
from django.core.validators import MinValueValidator, MaxValueValidator

from directory.models import WasteBank

class WasteBankForm(ModelForm):
    class Meta:
        model = WasteBank
        fields = [
            "name",
            "address",
            "contact_number",
            "email",
            "latitude",
            "longitude",
        ]

        labels = {
            "name": "Nama Bank Sampah",
            "address": "Alamat",
            "contact_number": "Nomor Kontak",
            "email": "Email",
            "latitude": "Latitude",
            "longitude": "Longitude",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Nama Bank Sampah",
                    "maxlength": 255,
                }
            ),
            "address": Textarea(
                attrs={
                    "placeholder": "Jl. Contoh Alamat No. 123, Kota Contoh",
                    "rows": 3,
                }
            ),
            "contact_number": TextInput(
                attrs={
                    "placeholder": "08xxxxxxxxxx",
                    "maxlength": 15,
                }
            ),
            "email": EmailInput(
                attrs={
                    "placeholder": "contoh@gmail.com",
                }
            ),
            "latitude": NumberInput(
                attrs={
                    "step": "0.000001",
                    "placeholder": "Contoh: 87.362",
                }
            ),
            "longitude": NumberInput(
                attrs={
                    "step": "0.000001",
                    "placeholder": "Contoh: 87.362",
                }
            ),
        }
