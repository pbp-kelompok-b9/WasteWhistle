from django import forms


class ReportForm(forms.Form):
    title = forms.CharField(
        label="Judul laporan", max_length=120,
        help_text="Maksimal 120 karakter. Tulis kondisi utama yang kamu temukan.",
        widget=forms.TextInput(attrs={"placeholder": "Contoh: Tumpukan sampah di dekat halte"}),
    )
    description = forms.CharField(
        label="Deskripsi", max_length=2000,
        help_text="Maksimal 2.000 karakter. Jelaskan jenis, perkiraan jumlah, dan kondisi sampah.",
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Ceritakan kondisi sampah di lokasi…"}),
    )
    location_note = forms.CharField(
        label="Patokan lokasi", max_length=200, required=False,
        help_text="Opsional, maksimal 200 karakter. Sebutkan bangunan atau tempat terdekat.",
        widget=forms.TextInput(attrs={"placeholder": "Contoh: Di samping gerbang kampus"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.error_messages.update({
                "required": "Bagian ini wajib diisi.",
                "max_length": "Maksimal %(limit_value)s karakter (saat ini %(show_value)s).",
            })
            field.widget.attrs["aria-describedby"] = f"{name}-help {name}-errors"
