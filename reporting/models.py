from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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
