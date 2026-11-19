from django.utils.html import strip_tags
from rest_framework import serializers

from education.models import WasteGuide, DecompositionInfo, MythOrFact, QuizAttempt, QuizQuestion

class WasteGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteGuide
        fields = [
            "id", "name", "category", "description", "handling_instruction",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_description(self, value):
        return strip_tags(value)

    def validate_category(self, value):
        return strip_tags(value)

    def validate_handling_instruction(self, value):
        return strip_tags(value)

class DecompositionInfoSerializer(serializers.ModelSerializer):
    formatted_duration = serializers.SerializerMethodField()
    bar_percent = serializers.SerializerMethodField()
    bar_level = serializers.SerializerMethodField()

    class Meta:
        models = DecompositionInfo
        fields = [
            "id", "material_name", "estimated_days",
        ]
        read_only_fields = ["id"]

    def validate_material_name(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Material name cannot be empty.")
        return value
    
    def get_formatted_duration(self, obj):
        return obj.formatted_duration

    def get_bar_percent(self, obj):
        return obj.bar_percent

    def get_bar_level(self, obj):
        return obj.bar_level

class MythOrFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = MythOrFact
        fields = [
            "id", "statement", "is_myth", "explanation", "source_url"
        ]
        read_only_fields = ["id"]
    def validate_statement(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Statement cannot be empty.")
        return value
    def validate_explanation(self, value):
        return strip_tags(value)    

class QuizQuestionSerializer(serializers.ModelSerializer):
    item = WasteGuideSerializer(read_only=True)
    class Meta:
        model = QuizQuestion
        fields = [
            "id", "item",
        ]
        read_only_fields = ["id"]

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id", "user", "attempt_date", "score"
        ]
        read_only_fields = [
            "id", "user", "attempt_date", "score"
        ]
