from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from rewards.services import tambah_poin
from django.db import models


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="waste_reports",
    )
    title = models.CharField(max_length=120)
    description = models.TextField(max_length=2000)
    location_note = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    submission_id = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title
    

@receiver(post_save, sender=Report)
def reward_points_on_report(sender, instance, created, **kwargs):
    """Otomatis beri +10 poin saat user membuat laporan baru."""
    if created:
        tambah_poin(
            user=instance.reporter,
            jumlah=10,
            alasan=f"Membuat laporan: {instance.title}",
            referensi=f"report-{instance.pk}"  # Mencegah duplikasi poin untuk laporan yang sama
        )
