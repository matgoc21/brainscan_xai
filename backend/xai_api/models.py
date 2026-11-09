from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    identifier = models.CharField(max_length=100, unique=True, verbose_name = "ID/PESEL")
    first_name = models.CharField(max_length=100, blank=True, verbose_name = "Imię")
    last_name = models.CharField(max_length=100, blank = True, verbose_name="Nazwisko")
    age = models.IntegerField(null=True,blank=True,verbose_name="Wiek")
    gender = models.CharField(max_length=20, blank=True, verbose_name="Płeć")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.identifier}] {self.first_name} {self.last_name} {self.age}".strip()

class ScanAnalysis(models.Model):
    CLASS_CHOICES = [
        ('glioma', 'Glejak'),
        ('meningioma', 'Oponiak'),
        ('notumor', 'Brak guza'),
        ('pituitary', 'Guz przysadki'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scans')
    # patient_id = models.CharField(max_length=100, default='Anonimowy')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='scans')
    original_image = models.ImageField(upload_to='scans/original/')
    heatmap_image = models.ImageField(upload_to = 'scans/heatmaps/', null=True, blank=True)
    predicted_class = models.CharField(max_length=50, choices=CLASS_CHOICES)
    confidence_percent = models.FloatField()
    propabilities = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.patient.identifier}] {self.predicted_class} ({self.confidence_percent}%) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"