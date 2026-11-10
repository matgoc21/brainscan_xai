from rest_framework import serializers
from .models import ScanAnalysis, Patient
class MRIUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'identifier', 'first_name', 'last_name', 'age', 'gender']

class ScanAnalysisSerializer(serializers.ModelSerializer):

    patient = PatientSerializer(read_only=True)
    class Meta:
        model = ScanAnalysis
        fields = ['id', 
                'patient',
                #'patient_id', 
                'original_image', 
                'heatmap_image', 
                'predicted_class',
                'confidence_percent',
                'probabilities',
                'created_at',
                ]
        read_only_fields = ['id','predicted_class', 'confidence_percent', 'prbabilities', 'created_at', 'heatmap_image']