from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Address, Client
from accounts.serializers.AccountSerializers import AccountLoginSerializer, CreateAddressSerializer, CreateClientSerializer, DetailUserSerializer, RegisterAccountSerializer

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
                'id': user.id,
                'email': user.email,
            }
        }, status=200)


class AccountDetailViewset(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = DetailUserSerializer
    permission_classes = [IsAuthenticated]



class CreateClientViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Client.objects.all()
    serializer_class = CreateClientSerializer
    permission_classes = [IsAuthenticated]

class CreateAddressViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Address.objects.all()
    serializer_class = CreateAddressSerializer
    permission_classes = [IsAuthenticated]


