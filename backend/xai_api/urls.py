from django.urls import path
from .views import AnalyzeMRIView, ScanListCreateView, ScanDetailView

urlpatterns = [
    path('analyze/', AnalyzeMRIView.as_view(), name='analyze-mri'),
    path('scans/', ScanListCreateView.as_view(), name='scan-list-create'),
    path('scans/<int:pk>/', ScanDetailView.as_view(), name='scan-detail'),
]