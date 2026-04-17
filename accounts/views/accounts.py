# accounts/views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from accounts.serializers.RegisterAccountSerializer import AccountLoginSerializer, RegisterAccountSerializer

User = get_user_model()

class RegisterAccountViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]


class AccountLoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    serializer_class = AccountLoginSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_200_OK)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [IsAuthenticated]