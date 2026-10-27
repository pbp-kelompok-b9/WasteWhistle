from django.db import models
    
    
class Reward(models.Model):
    KATEGORI_CHOICES = [
        ("transportasi", "Transportasi"),
        ("belanja", "Belanja"),
        ("lingkungan", "Lingkungan"),
        ("acara", "Acara"),
        ("lainnya", "Lainnya"),
    ]

    nama = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True)
    kategori = models.CharField(
        max_length=20, choices=KATEGORI_CHOICES, default="lainnya"
    )
    harga_poin = models.PositiveIntegerField()
    stok = models.PositiveIntegerField(default=0)
    gambar = models.URLField(max_length=500, blank=True)
    level_minimal = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["harga_poin", "nama"]

    def __str__(self):
        return self.nama
