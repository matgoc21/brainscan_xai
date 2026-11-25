from PIL import Image, UnidentifiedImageError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.shortcuts import render
from django.db.models import Q
from rest_framework.parsers import FormParser , MultiPartParser
from .serializers import MRIUploadSerializer, ScanAnalysisSerializer, PatientSerializer
from .xai_service import generate_gradcam_and_predict
from .models import ScanAnalysis, Patient

MAX_UPLOAD_SIZE_MB = 15
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
   # parser_classes = [MultiParser, FormParser]

    # def get_queryset(self):
    #     user = self.request.user
    #     queryset = ScanAnalysis.objects.filter(user=user).select_related('patient')
    #     search_query = self.request.query_params.get('search')
    #     predicted_class = self.request.query_params.get('class')
    #     if predicted_class:
    #         queryset = queryset.filter(predicted_class__iexact=predicted_class)       
    #     if search_query:
    #         queryset = queryset.filter(patient_id__icontains=search_query)

    #     return queryset
    def get_queryset(self):
        queryset = ScanAnalysis.objects.filter(user=self.request.user).select_related('patient')

        target_class = self.request.query_params.get('class')
        if target_class:
            queryset = queryset.filter(predicted_class__iexact=target_class)

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(patient__identifier__icontains=search_query)
                | Q(patient__first_name__icontains=search_query)
                | Q(patient__last_name__icontains=search_query)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        patient_id = request.data.get('patient_identifier', '').strip()

        if not patient_id:
            return Response({"error": "Podanie ID pacjenta jest wymagane."},status=status.HTTP_400_BAD_REQUEST,)

        if not image_file:
            return Response({"error": "Brak pliku o kluczu 'image' w żądaniu."}, status=status.HTTP_400_BAD_REQUEST,)

        if image_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            return Response({"error": f"Plik jest za duży. Maksymalny rozmiar to {MAX_UPLOAD_SIZE_MB} MB."}, status = status.HTTP_400_BAD_REQUEST,)


        try:
            with Image.open(image_file) as img:
                img.verify()
            image_file.seek(0)
        except (UnidentifiedImageError, Exception):
            return Response({"error": "Przesłany plik nie jest prawidłowym obrazem. Wymagany format pliku to .jpg lub .png ."}, status=status.HTTP_400_BAD_REQUEST)

        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        gender = request.data.get('gender', '').strip().upper()
        raw_age = request.data.get('age', '').strip()

        age = None

        if raw_age: 
            if not raw_age.isdigit() or not (0 <= int(raw_age) <= 130):
                return Response({"error": "Wiek pacjenta musi być liczbą całkowitą z przedziału od 0 do 130."}, status=status.HTTP_400_BAD_REQUEST,)
            age = int(raw_age)

        if gender and gender not in {'M', 'K', 'INNE'}:
            return Response({"error": "Płeć powinna mieć wartość 'M', 'K', 'INNE'"}, status=status.HTTP_400_BAD_REQUEST,)

        existing_patient = Patient.objects.filter(identifier=patient_id).first()

        if existing_patient:
            conflicts=[]
            if first_name and existing_patient.first_name and first_name.lower() != existing_patient.first_name.lower():
                conflicts.append(f"Imię w bazie: '{existing_patient.first_name}'.")
            if last_name and existing_patient.last_name and last_name.lower() != existing_patient.last_name.lower():
                conflicts.append(f"Nazwisko w bazie: '{existing_patient.last_name}.'")
            if age is not None and existing_patient.age is not None and age != existing_patient.age:
                conflicts.append(f"Wiek w bazie: '{existing_patient.age}'.")
            if gender and existing_patient.gender and gender != existing_patient.gender:
                conflicts.append(f"Płeć w bazie: '{existing_patient.age}'.")

            if conflicts:
                conflict_str = ", ".join(conflicts)

                return Response( 
                    {
                        "error": (
                            f"Pacjent o ID '{patient_id}' już istnieje w bazie danych z innymi danymi"
                            f"Niezgodne pola: {conflict_str}"
                            f"Popraw ID pacjenta lub pozostaw pola danych puste, aby przypisać skan do istniejącego pacjenta"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            updated = False
            if first_name and not existing_patient.first_name:
                existing_patient.first_name = first_name
                updated = True
            if last_name and not existing_patient.last_name:
                existing_patient.last_name = last_name
                updated = True
            if age and not existing_patient.age:
                existing_patient.age = age
                updated = True
            if gender and not existing_patient.gender:
                existing_patient.gender = gender
                updated = True
            if updated:
                existing_patient.save()
            patient = existing_patient
        else:
            patient = Patient.objects.create(
                identifier = patient_id,
                first_name=first_name,
                last_name=last_name,
                age=age,
                gender=gender,
            )
        analysis_result = generate_gradcam_and_predict(image_file)
        image_file.seek(0)

        scan = ScanAnalysis.objects.create(
            user=request.user,
            patient=patient,
            original_image=image_file,
            heatmap_image=analysis_result['heatmap_file'],
            predicted_class=analysis_result['prediction'],
            confidence_percent=analysis_result['confidence'],
            probabilities=analysis_result['probabilities'],
        )
        

        # patient, created = Patient.objects.get_or_create(
        #     identifier=patient_id,
        #     defaults={
        #         'first_name': request.data.get('first_name', ''),
        #         'last_name': request.data.get('last_name', ''),
        #         'age':  request.data.get('age') if request.data.get('age') else None,
        #         'gender': request.data.get('gender', '')
        #     }
        # )

        # analysis_result = generate_gradcam_and_predict(image_file)

        # scan = ScanAnalysis.objects.create(
        #     user = request.user,
        #     #patient_id=patinet_id,
        #     patient=patient,
        #     original_image=image_file,
        #     heatmap_image=analysis_result['heatmap_file'],
        #     predicted_class=analysis_result['prediction'],
        #     confidence_percent=analysis_result['confidence'],
        #     probabilities=analysis_result['probabilities']
        # )

        serializer = self.get_serializer(scan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ScanDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/scans/<id>/ - zwraca szczegóły pojedynczego badania
    DELETE /api/scans/<id>/ - usuwa badanie z bazy danych
    """

    serializer_class = ScanAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScanAnalysis.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        patient = instance.patient
        if instance.original_image:
            instance.original_image.delete(save=False)
        if instance.heatmap_image:
            instance.heatmap_image.delete(save=False)
        instance.delete()

        if not patient.scans.exists():
            patient.delete()
class PatientListView(generics.ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        
        return Patient.objects.filter(scans__user=self.request.user).distinct()