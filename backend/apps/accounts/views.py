from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from apps.common.permissions import IsAdmin
from apps.audit_logs.services import log_action
from apps.audit_logs.models import AuditLog

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        log_action(
            user=request.user,
            action=AuditLog.Action.LOGOUT,
            model_name='User',
            object_id=request.user.id,
            description=f'Logout user {request.user.username}',
            request=request
        )
        return Response({'message': 'Logout logged successfully.'})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(serializer.validated_data.get('password', ''))
        user.save()
