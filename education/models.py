from django.db import models
from django.conf import settings
from django.utils import timezone
import math
import uuid

def _plural(number, word):
    return f"{number:,} {word}"

class WasteGuide(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CATEGORY_CHOICES = [
        ("organik", "Sampah Organik"),
        ("anorganik", "Sampah Anorganik"),
        ("kertas", "Sampah Kertas"),
        ("residu", "Sampah Residu"),
        ("b3", "Sampah B3"),
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
    
    def __str__(self):
        return self.material_name

    @property
    def formatted_duration(self):
        days = self.estimated_days
 
        if days < 30:
            return _plural(days, "hari")
 
        if days < 365:
            months = min(round(days / 30), 11)
            return _plural(months, "bulan")
 
        years = round(days / 365)
        return _plural(years, "tahun")

    @property
    def bar_percent(self):
        longest_days = 365 * 1_000_000          
        days = max(self.estimated_days, 1)      
        percent = math.log10(days) / math.log10(longest_days) * 100
        return max(5, min(round(percent), 100)) 

    @property
    def bar_level(self):
        if self.estimated_days < 365:           
            return "short"
        if self.estimated_days < 365 * 300:     
            return "medium"
        return "long"
 

class QuizQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.OneToOneField(
        "WasteGuide",
        on_delete=models.CASCADE,
        related_name="quiz_question",
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
    score = models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "attempt_date"],
                name="one_quiz_per_day",
            )
        ]
    def __str__(self):
        return f"{self.user} - {self.attempt_date}"
