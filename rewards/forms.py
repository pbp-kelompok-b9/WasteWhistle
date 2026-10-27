from django.forms import ModelForm, TextInput, Textarea, URLInput, NumberInput
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from .models import Reward


class RewardForm(ModelForm):
    class Meta:
        model = Reward
        fields = ["nama", "deskripsi", "harga_poin", "stok", "gambar"]

        labels = {
            "nama": "Nama reward",
            "deskripsi": "Deskripsi reward",
            "harga_poin": "Poin yang dibutuhkan",
            "stok": "Jumlah stok",
            "gambar": "URL gambar reward",
        }

        widgets = {
            "nama": TextInput(attrs={
                "placeholder": "ex: Voucher KopiKafe Rp 25,000",
            }),
            "deskripsi": Textarea(attrs={
                "placeholder": "Deskripsikan reward",
                "rows": 3,
            }),
            "harga_poin": NumberInput(attrs={
                "placeholder": "ex: 100",
                "min": 1,
            }),
            "stok": NumberInput(attrs={
                "placeholder": "ex: 50",
                "min": 0,
            }),
            "gambar": URLInput(attrs={
                "placeholder": "ex: https://drive.google.com/thumbnail?id=...&sz=w1000",
            }),
        }

    def clean_nama(self):
        nama = strip_tags(self.cleaned_data["nama"]).strip()
        if len(nama) < 3:
            raise ValidationError("Nama reward minimal 3 karakter.")
        return nama

    def clean_deskripsi(self):
        return strip_tags(self.cleaned_data.get("deskripsi", "")).strip()

    def clean_harga_poin(self):
        harga = self.cleaned_data["harga_poin"]
        if harga < 1:
            raise ValidationError("Poin yang dibutuhkan minimal 1.")
        return harga