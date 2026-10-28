from django import forms


class ReportForm(forms.Form):
    title = forms.CharField(
        label="Judul Laporan", max_length=120,
        help_text="Maksimal 120 karakter. Tulis kondisi utama yang kamu temukan.",
        widget=forms.TextInput(attrs={"placeholder": "Contoh: Tumpukan sampah di dekat halte"}),
    )
    description = forms.CharField(
        label="Deskripsi", max_length=2000,
        help_text="Maksimal 2.000 karakter. Jelaskan jenis, perkiraan jumlah, dan kondisi sampah.",
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Ceritakan kondisi sampah di lokasi…"}),
    )
    location_note = forms.CharField(
        label="Patokan Lokasi", max_length=200, required=False,
        help_text="Opsional, maksimal 200 karakter. Sebutkan bangunan atau tempat terdekat.",
        widget=forms.TextInput(attrs={"placeholder": "Contoh: Di samping gerbang kampus"}),
    )
    latitude = forms.DecimalField(
        label="Latitude (lintang)", max_digits=9, decimal_places=6,
        min_value=-90, max_value=90,
        help_text="Angka -90 sampai 90, maksimal 6 angka desimal.",
        widget=forms.NumberInput(attrs={"step": "0.000001", "placeholder": "Contoh: -6.362000"}),
    )
    longitude = forms.DecimalField(
        label="Longitude (bujur)", max_digits=9, decimal_places=6,
        min_value=-180, max_value=180,
        help_text="Angka -180 sampai 180, maksimal 6 angka desimal.",
        widget=forms.NumberInput(attrs={"step": "0.000001", "placeholder": "Contoh: 106.827000"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.error_messages.update({
                "required": "Bagian ini wajib diisi.",
                "max_length": "Maksimal %(limit_value)s karakter (saat ini %(show_value)s).",
            })
            if name in ("latitude", "longitude"):
                field.error_messages.update({
                    "required": "Pilih titik di peta atau isi kedua koordinat lokasi.",
                    "invalid": "Masukkan koordinat berupa angka yang valid.",
                    "min_value": "Koordinat minimal %(limit_value)s.",
                    "max_value": "Koordinat maksimal %(limit_value)s.",
                    "max_decimal_places": "Gunakan maksimal 6 angka desimal.",
                    "max_digits": "Koordinat terlalu panjang. Gunakan maksimal 6 angka desimal.",
                })
            field.widget.attrs["aria-describedby"] = f"{name}-help {name}-errors"
            field.widget.attrs["class"] = "report-input"
