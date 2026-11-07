from django.db import models
from django.contrib.auth.models import User

class ScanAnalysis(models.Model):
    CLASS_CHOICES = [
        ('glioma', 'Glejak'),
        ('meningioma', 'Oponiak'),
        ('notumor', 'Brak guza'),
        ('pituitary', 'Guz przysadki'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scans')
    patient_id = models.CharField(max_length=100, default='Anonimowy')
    original_image = models.ImageField(upload_to='scans/original/')
    heatmap_image = models.ImageField(upload_to = 'scans/heatmaps/', null=True, blank='True')
    predicted_class = models.CharField(max_length=50, choices=CLASS_CHOICES)
    confidence_percent = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.patient_id}] {self.predicted_class} ({self.confidence_percent}%) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"