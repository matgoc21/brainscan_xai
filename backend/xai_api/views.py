from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.shortcuts import render
from rest_framework.parsers import MultiParser, FormParser
from .serializers import MRIUploadSerializer, ScanAnalysisSerializer
from .xai_service import generate_gradcam_and_predict
from .models import ScanAnalysis


# Create your views here.
#Old
class AnalyzeMRIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MRIUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['image']

            try:
                result = generate_gradcam_and_predict(uploaded_file)
                return Response({
                    "status": "success",
                    "data": result
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "status": "error",
                    "message": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ScanListCreateView(generics.ListCreateAPIView):
    """
    GET /api/scans/ - zwraca listę badań zalogowanego użytkownika
    POST /api/scans/ - przyjmuje plik skanu, wykonuje analizę
    """

    serializer_class = ScanAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        queryset = ScanAnalysis.objects.filter(user=user)

        target_class = self.request.query_params.get('class')
        if target_class:
            queryset = queryset.filter(predicted_class__iexact=target_class)

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(patient_id__icontains=search_query)

        return queryset

    def create(self, request, *args, **kwargs):
        image_file = rquest.FILES.get('image')
        patinet_id = request.data.get('patient_identifier', 'Anonimowy')

        if not image_file:
            return Response({"error": "Brak pliku o kluczu 'image' w żądaniu."}, status=status.HTTP_400_BAD_REQUEST)

        analysis_result = generate_gradcam_and_predict(image_file)

        scan = ScanAnalysis.objects.create(
            user = request.user,
            patient_id=patinet_id,
            original_image=image_file,
            heatmap_image=analysis_result['heatmap_file'],
            predicted_class=analysis_result['prediction'],
            confidence_percent=analysis_result['confidence']
        )

        serializer = self.get_serializer(scan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ScanDetailView(generics.RetrieveAPIView):
    """
    GET /api/scans/<id>/ - zwraca szczegóły pojedynczego badania
    DELETE /api/scans/<id>/ - usuwa badanie z bazy danych
    """

    serializer_class = ScanAnalysisSerializer
    permission_classes = [permissions.IsAuthnenticated]

    def get_queryset(self):
        return ScanAnalysis.objects.filter(user=self.request.user)