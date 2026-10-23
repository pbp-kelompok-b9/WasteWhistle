from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class WasteGuide(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CATEGORY_CHOICES = [
        ("organic", "Organic Waste"),
        ("inorganic", "Inorganic Waste"),
        ("recycleable", "Recycleable Waste"),
        ("residual", "Residual Waste"),
        ("hazardous", "Hazardous Waste"),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    handling_instruction = models.TextField()

    def __str__(self):
        return self.name

class MythOrFact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    statement = models.CharField(max_length=255)
    is_myth = models.BooleanField()
    explanation = models.TextField()
    source_url = models.URLField(blank=True)
    def __str__(self):
            return self.statement

class DecompositionInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material_name = models.CharField(max_length=100)
    estimated_days = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    source_url = models.URLField(blank=True)

    def __str__(self):
        return self.material_name

    @property
    def formatted_duration(self):
        days = self.estimated_days

        if days < 30:
            return f"{days} days"
        elif days < 365:
            months = round(days / 30)
            return f"{months} months"
        else:
            years = round(days / 365)
            return f"{years} years"

class QuizQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        WasteGuide,
        on_delete=models.CASCADE,
        related_name="quiz_questions"
    )

    def __str__(self):
        return self.item.name

class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts"
    )
    attempt_date = models.DateField(default=timezone.localdate)
    constraints = [
        models.UniqueConstraint(
            fields=["user", "attempt_date"],
            name="one_quiz_per_day"
        )
    ]
    def __str__(self):
        return f"{self.user} - {self.completed_at}"