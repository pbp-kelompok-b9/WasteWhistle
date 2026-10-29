from django.forms import ModelForm, TextInput, Textarea, Select, NumberInput, TypedChoiceField, URLInput
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from .models import DecompositionInfo, MythOrFact, WasteGuide

def clean_plain_text(value, label):
    cleaned = strip_tags(value).strip()
    if not cleaned:
        raise ValidationError(
            f"{label} tidak boleh kosong atau hanya mengandung tag HTML."
        )
    return cleaned

class WasteGuideForm(ModelForm):
    class Meta:
        model = WasteGuide
        fields = ("name", "category", "description", "handling_instruction")
        labels = {
            "name": "Nama sampah",
            "category": "Kategori sampah",
            "description": "Deskripsi sampah",
            "handling_instruction": "Instruksi penanganan sampah",
        }
        widgets = {
            "name": TextInput(attrs={"maxlength": 100}),
            "category": Select(),
            "description": Textarea(attrs={"rows": 3}),
            "handling_instruction": Textarea(attrs={"rows": 3}),
        }

    def clean_name(self):
        return clean_plain_text(self.cleaned_data["name"], "Nama sampah")

    def clean_description(self):
        return clean_plain_text(self.cleaned_data["description"], "Deskripsi sampah")

    def clean_handling_instruction(self):
        return clean_plain_text(
            self.cleaned_data["handling_instruction"], "Instruksi penanganan sampah"
        )


class DecompositionInfoForm(ModelForm):
    class Meta:
        model = DecompositionInfo
        fields = ("material_name", "estimated_days")
        labels = {
            "material_name": "Nama material",
            "estimated_days": "Perkiraan waktu penguraian (hari)",
        }
        widgets = {
            "material_name": TextInput(attrs={"maxlength": 100}),
            "estimated_days": NumberInput(attrs={"min": 0}),
        }

    def clean_material_name(self):
        return clean_plain_text(
            self.cleaned_data["material_name"], "Nama material"
        )


class MythOrFactForm(ModelForm):

    is_myth = TypedChoiceField(
        choices=MythOrFact.CLASSIFICATION_CHOICES,
        coerce=lambda value: value == "True",
        label="Klasifikasi (mitos/fakta)",
        widget=Select(),
    )

    class Meta:
        model = MythOrFact
        fields = ("statement", "is_myth", "explanation", "source_url")
        labels = {
            "statement": "Pernyataan terkait sampah",
            "explanation": "Penjelasan",
            "source_url": "Sumber pernyataan (opsional)",
        }
        widgets = {
            "statement": TextInput(attrs={"maxlength": 255}),
            "explanation": Textarea(attrs={"rows": 3}),
            "source_url": URLInput(attrs={"placeholder": "https://..."}),
        }

    def clean_statement(self):
        return clean_plain_text(
            self.cleaned_data["statement"], "Pernyataan terkait sampah"
        )

    def clean_explanation(self):
        return clean_plain_text(self.cleaned_data["explanation"], "Penjelasan")
