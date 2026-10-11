from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MRIUploadSerializer
from django.shortcuts import render
from .xai_service import generate_gradcam_and_predict


# Create your views here.
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