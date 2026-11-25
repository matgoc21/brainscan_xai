from django.urls import path
from .views import AnalyzeMRIView, ScanListCreateView, ScanDetailView, PatientListView

urlpatterns = [
    path('analyze/', AnalyzeMRIView.as_view(), name='analyze-mri'),
    path('scans/', ScanListCreateView.as_view(), name='scan-list-create'),
    path('scans/<int:pk>/', ScanDetailView.as_view(), name='scan-detail'),
    path('patients/', PatientListView.as_view(), name='patient-list'),
]