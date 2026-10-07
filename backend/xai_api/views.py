from rest_framework import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MRIUploadSerializer
from django.shortcuts import render

# Create your views here.
class AnalyzeMRIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MRIUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['image']

            return Response(
                {"message": f"Plik {uploaded_file.name} został pomyślnie odebrany."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)