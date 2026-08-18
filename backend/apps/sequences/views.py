from rest_framework import viewsets
from .models import DocumentSequence
from .serializers import DocumentSequenceSerializer
from apps.common.permissions import IsAdmin

class DocumentSequenceViewSet(viewsets.ModelViewSet):
    queryset = DocumentSequence.objects.all()
    serializer_class = DocumentSequenceSerializer
    permission_classes = [IsAdmin]
