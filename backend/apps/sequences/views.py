from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import DocumentSequence
from .serializers import DocumentSequenceSerializer

class DocumentSequenceViewSet(viewsets.ModelViewSet):
    queryset = DocumentSequence.objects.all()
    serializer_class = DocumentSequenceSerializer
    permission_classes = [IsAdminUser]
