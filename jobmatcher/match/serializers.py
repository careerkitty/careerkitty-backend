from rest_framework import serializers

class JobDescriptionSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    required_skills = serializers.ListField(child=serializers.CharField())
    education = serializers.CharField()
    years_of_experience = serializers.CharField()
    responsibilities = serializers.CharField()
    file = serializers.FileField()  # Updated to FileField

class ResumeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    skills = serializers.ListField(child=serializers.CharField())
    education = serializers.CharField()
    experience = serializers.CharField()
    file = serializers.FileField()  # Updated to FileField

class MatchSerializer(serializers.Serializer):
    job_desc_id = serializers.CharField(max_length=255)
    resume_id = serializers.CharField(max_length=255)
    match_score = serializers.FloatField()
    missing_skills = serializers.ListField(child=serializers.CharField())
    feedback = serializers.CharField()
