from django import forms
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

class EducationModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            current_class = field.widget.attrs.get("class", "")
            classes = current_class.split()
            if "education-admin-input" not in classes:
                classes.append("education-admin-input")
            field.widget.attrs["class"] = " ".join(classes)

class WasteGuideForm(EducationModelForm):
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
            "name": forms.TextInput(attrs={"maxlength": 100}),
            "category": forms.Select(),
            "description": forms.Textarea(attrs={"rows": 3}),
            "handling_instruction": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_name(self):
        return clean_plain_text(self.cleaned_data["name"], "Nama sampah")

    def clean_description(self):
        return clean_plain_text(self.cleaned_data["description"], "Deskripsi sampah")

    def clean_handling_instruction(self):
        return clean_plain_text(
            self.cleaned_data["handling_instruction"], "Instruksi penanganan sampah"
        )


class DecompositionInfoForm(EducationModelForm):
    class Meta:
        model = DecompositionInfo
        fields = ("material_name", "estimated_days")
        labels = {
            "material_name": "Nama material",
            "estimated_days": "Perkiraan waktu penguraian (hari)",
        }
        widgets = {
            "material_name": forms.TextInput(attrs={"maxlength": 100}),
            "estimated_days": forms.NumberInput(attrs={"min": 0}),
        }

    def clean_material_name(self):
        return clean_plain_text(
            self.cleaned_data["material_name"], "Nama material"
        )


class MythOrFactForm(EducationModelForm):

    is_myth = forms.TypedChoiceField(
        choices=MythOrFact.CLASSIFICATION_CHOICES,
        coerce=lambda value: value == "True",
        label="Klasifikasi (mitos/fakta)",
        widget=forms.Select(),
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
            "statement": forms.TextInput(attrs={"maxlength": 255}),
            "explanation": forms.Textarea(attrs={"rows": 3}),
            "source_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }

    def clean_statement(self):
        return clean_plain_text(
            self.cleaned_data["statement"], "Pernyataan terkait sampah"
        )

    def clean_explanation(self):
        return clean_plain_text(self.cleaned_data["explanation"], "Penjelasan")
