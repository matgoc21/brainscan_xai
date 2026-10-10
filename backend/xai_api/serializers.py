from rest_framework import serializers
class MRIUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

