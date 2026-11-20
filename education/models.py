from django.db import IntegrityError, models, transaction
from django.conf import settings
from django.utils import timezone
import math
import uuid

def _format_duration(number, unit):
    return f"{number:,}".replace(",", ".") + f" {unit}"

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
    CLASSIFICATION_CHOICES = (
        (True, "Mitos"),
        (False, "Fakta"),
    )
    statement = models.CharField(max_length=255)
    is_myth = models.BooleanField(choices=CLASSIFICATION_CHOICES, verbose_name="Klasifikasi")
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
            return _format_duration(days, "hari")
 
        if days < 365:
            months = min(round(days / 30), 11)
            return _format_duration(months, "bulan")
 
        years = round(days / 365)
        return _format_duration(years, "tahun")

    @property
    def bar_percent(self):
        longest_days = 365 * 1_000_000          
        days = max(self.estimated_days, 1)      
        percent = math.log10(days) / math.log10(longest_days) * 100
        return max(0, min(round(percent), 100))

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
    QUIZ_SIZE = 3

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts"
    )
    attempt_date = models.DateField(default=timezone.localdate)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    question_ids = models.JSONField(default=list)
    answers = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "attempt_date"],
                name="one_quiz_per_day",
            )
        ]
    def __str__(self):
        return f"{self.user} - {self.attempt_date}"

    @classmethod
    def start_daily(cls, user, attempt_date):
        attempt = cls.objects.filter(user=user, attempt_date=attempt_date).first()
        if attempt and attempt.score is not None:
            return attempt

        if attempt and attempt.has_valid_questions():
            return attempt

        question_ids = list(
            QuizQuestion.objects.order_by("?").values_list("id", flat=True)[:cls.QUIZ_SIZE]
        )
        if len(question_ids) != cls.QUIZ_SIZE:
            return None
        question_ids = [str(question_id) for question_id in question_ids]

        if attempt:
            attempt.question_ids = question_ids
            attempt.answers = {}
            attempt.save(update_fields=["question_ids", "answers"])
            return attempt

        try:
            with transaction.atomic():
                return cls.objects.create(
                    user=user,
                    attempt_date=attempt_date,
                    question_ids=question_ids,
                )
        except IntegrityError:
            return cls.objects.get(user=user, attempt_date=attempt_date)

    def has_valid_questions(self):
        if (
            not isinstance(self.question_ids, list)
            or len(self.question_ids) != self.QUIZ_SIZE
            or len(set(map(str, self.question_ids))) != self.QUIZ_SIZE
        ):
            return False
        return QuizQuestion.objects.filter(pk__in=self.question_ids).count() == self.QUIZ_SIZE

    def get_questions(self):
        if not self.has_valid_questions():
            return []
        found = {
            str(question.id): question
            for question in QuizQuestion.objects.filter(
                id__in=self.question_ids,
            ).select_related("item")
        }
        return [
            found[str(question_id)]
            for question_id in self.question_ids
            if str(question_id) in found
        ]
