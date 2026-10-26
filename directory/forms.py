from django.forms import ModelForm, TextInput, Textarea, EmailInput

from directory.models import WasteBank

class WasteBankForm(ModelForm):
    class Meta:
        model = WasteBank
        fields = [
            "name",
            "address",
            "contact_number",
            "email",
        ]

        labels = {
            "name": "Nama Bank Sampah",
            "address": "Alamat",
            "contact_number": "Nomor Kontak",
            "email": "Email",
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
                    "placeholder": "example@gmail.com",
                }
            ),
        }
