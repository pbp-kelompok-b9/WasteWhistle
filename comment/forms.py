from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "report-input text-xs",
                    "placeholder": "Tulis tanggapan atau catatan lokasi kamu di sini…",
                    "rows": 3,
                    "required": True,
                }
            ),
        }
