from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=255, required=False)
    resume_file = serializers.FileField(required=False)
