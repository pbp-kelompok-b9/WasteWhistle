from django.db import models

class Reward(models.Model):
    nama = models.CharField(max_length=100)
    deskripsi = models.TextField(blank=True)
    harga_poin = models.PositiveIntegerField()
    stok = models.PositiveIntegerField(default=0)
    gambar = models.URLField(blank=True)  # pakai link dulu, lebih mudah

    def __str__(self):
        return self.nama
