from django.contrib import admin
from .models import (
    WasteGuide,
    MythOrFact,
    DecompositionInfo,
    QuizQuestion,
)

admin.site.register(WasteGuide)
admin.site.register(MythOrFact)
admin.site.register(DecompositionInfo)
admin.site.register(QuizQuestion)
