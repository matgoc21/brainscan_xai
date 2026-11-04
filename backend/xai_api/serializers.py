from rest_framework import serializers
from .models import ScanAnalysis
class MRIUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

class ScanAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanAnalysis
        fields = ['id', 
                'user',
                'patient_id', 
                'original_image', 
                'heatmap_image', 
                'predicted_class',
                'confidence_percent',
                'created_at',
                ]
        read_only_fields = ['id', 'user', 'confidence_percent', 'created_at', 'heatmap_image']