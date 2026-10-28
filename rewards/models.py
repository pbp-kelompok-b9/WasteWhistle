from django.db import models
from django.conf import settings
    
    
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


class PointTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="point_transactions",
    )
    jumlah = models.IntegerField()  # positif = masuk, negatif = keluar
    alasan = models.CharField(max_length=200)
    referensi = models.CharField(max_length=100, blank=True)  # contoh: "laporan-12"
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tanggal"]
        constraints = [
            # satu referensi hanya boleh memberi poin sekali per user
            models.UniqueConstraint(
                fields=["user", "referensi"],
                condition=~models.Q(referensi=""),
                name="unik_referensi_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} {self.jumlah:+d} ({self.alasan})"


class Redemption(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="redemptions",
    )
    reward = models.ForeignKey(
        Reward, on_delete=models.PROTECT, related_name="redemptions"
    )
    poin_dipakai = models.PositiveIntegerField()
    kode = models.CharField(max_length=20, blank=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tanggal"]

    def __str__(self):
        return f"{self.user} - {self.reward.nama}"