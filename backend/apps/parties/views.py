from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Party
from .serializers import PartySerializer
from apps.common.permissions import IsAccountant

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAccountant]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
