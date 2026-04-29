from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Account, Address, Client
from accounts.serializers.AccountSerializers import AccountLoginSerializer, AccountSerializer, CreateAddressSerializer, CreateClientSerializer, DetailUserSerializer, RegisterAccountSerializer

User = get_user_model()

class RegisterAccountViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]

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

class ClientDetailViewset(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = DetailUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)

class ClientViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Client.objects.all()
    serializer_class = CreateClientSerializer
    permission_classes = [IsAuthenticated]

class AddressViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Address.objects.all()
    serializer_class = CreateAddressSerializer
    permission_classes = [IsAuthenticated]

class AccountCreateView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        user = self.request.user
        is_admin = getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)

        if is_admin and 'owner' in self.request.data:
            serializer.save()
        else:
            serializer.save(owner=self.request.user)