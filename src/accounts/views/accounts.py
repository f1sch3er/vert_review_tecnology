from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Account, Address, Client
from accounts.serializers.AccountSerializers import AccountLoginSerializer, AccountSerializer, CreateAddressSerializer, CreateClientSerializer, DetailUserSerializer, RegisterAccountSerializer
from core.utils import is_admin

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

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = CreateClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request, *args, **kwargs):
        user = self.request.user
        if is_admin(user):
            return self.queryset.all()
        return self.queryset.filter(user=self.request.user)


    def create(self, request, *args, **kwargs):
        data_request = request.data.copy()

        target_user_id = data_request.get('user')

        if not is_admin(request.user):
            if not target_user_id:
                data_request['user'] = request.user.id

        else:
            data_request['user'] = target_user_id
        
        print(f"Data request after modification: {data_request}", flush=True)

        serializer = self.get_serializer(data=data_request)
        serializer.is_valid(raise_exception=True)
        print(f"Serializer validated data: {serializer.validated_data}", flush=True)
        serializer.save()

        self.headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=self.headers)
    

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