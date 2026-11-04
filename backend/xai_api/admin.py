from django.contrib import admin
from .models import ScanAnalysis

@admin.register(ScanAnalysis)
class ScanAnalysisAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'user', 'predicted_class', 'confidence_percent', 'created_at')
    list_filter = ('predicted_class', 'created_at')
    search_fields = ('patient_id', 'user__username')

# Register your models here.
