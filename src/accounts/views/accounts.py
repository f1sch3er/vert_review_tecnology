from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins, status
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Account, Client

from accounts.serializers.AccountSerializers import (
    AccountLoginSerializer,
    AccountReadSerializer,
    UserRegistrationResponseSerializer, 
    CreateClientSerializer, 
    RegisterAccountSerializer,
    AuthResponseSerializer
)

User = get_user_model()

class NewUserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        respose_serializer = UserRegistrationResponseSerializer(
            user,
            context={'request': request}
        )

        return Response(
            {
                "message": "Usuário registrado com sucesso! Bem-vindo ao nosso banco.",
                "data": respose_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

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
        
        response_serializer = AuthResponseSerializer(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user
            },
            context={'request': request}
        )

        return Response(response_serializer.data, status=status.HTTP_200_OK)


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
            serializer.save(user=User.objects.get(id=target_user_id))
        else:
            serializer.save(user=user)


class AccountMeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response({"detail": "Use o endpoint /me/ para ver sua conta."}, status=400)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        account = Account.objects.filter(owner__user=request.user).first()
        if not account:
            return Response({"detail": "Conta não encontrada."}, status=404)
        
        serializer = AccountReadSerializer(account)
        return Response(serializer.data)