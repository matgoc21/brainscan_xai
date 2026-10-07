from django.urls import path
from .views import AnalyzeMRIView

urlpatterns = [
    path('analyze/', AnalyzeMRIView.as_view(), name='analyze-mri'),
]