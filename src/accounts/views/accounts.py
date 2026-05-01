from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Account, Address, Client

from accounts.serializers.AccountSerializers import (
    AccountDetailSerializer,
    AccountLoginSerializer, 
    CreateClientSerializer, 
    RegisterAccountSerializer
)

User = get_user_model()

class NewUserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]


    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='check-email')
    def check_email_exists(self, request):
        email = request.query_params.get('email')
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists})
    


class AuthViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
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
                'id': user.id,
                'email': user.email,
            }
        }, status=200)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = CreateClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_any_admin:
            return Client.objects.all()
        return Client.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        target_user_id = self.request.data.get('user')

        if user.is_any_admin and target_user_id:
            serializer.save(user_id=target_user_id)
        else:
            serializer.save(user=user)   


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AccountDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Account.objects.select_related('owner__user', 'owner__address')
        
        if user.is_any_admin:
            return queryset.all()
        return queryset.filter(owner__user=user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        account = self.get_queryset().first()
        if not account:
            return Response({"detail": "Conta não encontrada."}, status=404)
        serializer = self.get_serializer(account)
        return Response(serializer.data)