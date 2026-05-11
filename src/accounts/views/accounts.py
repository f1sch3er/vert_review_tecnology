import logging

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
    FullUserProfileSerializer,
    UpsertUserProfileSerializer,
    UserRegistrationResponseSerializer, 
    CreateClientSerializer, 
    RegisterAccountSerializer,
    AuthResponseSerializer
)
from transactions.models import Transaction
from transactions.serializers.transactions_serializer import DepositKafkaSerializer, DepositTransactionSerializer, TransactionKafkaSerializer
from transactions.services.transaction_producer import TransactionProducer

User = get_user_model()

class NewUserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

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

    @action(detail=False, methods=['get'], url_path='has-profile')
    def user_has_profile(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'E-mail é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'Usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        has_profile = hasattr(user, 'client_profile')

        return Response({
            'has_profile': has_profile,
            'message': 'Perfil verificado com sucesso'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='check-email')
    def check_email_exists(self, request):
        email = request.query_params.get('email')
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists})
    


class AuthViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    serializer_class = AccountLoginSerializer
    authentication_classes = []
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

    def get_queryset(self):
        return Account.objects.filter(owner__user=self.request.user)
    
    def list(self, request):
        return Response({"detail": "Use o endpoint /me/ para ver sua conta."}, status=400)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        account = Account.objects.filter(owner__user=request.user).first()
        if not account:
            return Response({"detail": "Conta não encontrada."}, status=404)
        
        serializer = AccountReadSerializer(account)
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'], url_path='complete-profile')
    def complete_profile(self, request):
        data = request.data

        client, created = Client.objects.get_or_create(
            user=request.user,
            defaults={
                "birth_date": data.get("birth_date"),
                "document_number": data.get("document_number"),
                "document_type": data.get("document_type"),
                "phone_number": data.get("phone_number"),
            }
        )

        account = Account.objects.select_related(
            'owner__user',
            'owner__address'
        ).filter(owner=client).first()

        if not account:
            account = Account.objects.create(owner=client)

        serializer = UpsertUserProfileSerializer(
            instance=account,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=200)
    
    @action(detail=False, methods=['get', 'patch'], url_path='profile')
    def profile(self, request):
        account = Account.objects.select_related(
            'owner__user', 
            'owner__address'
        ).filter(owner__user=request.user).first()

        if not account:
            return Response({"detail": "Perfil não encontrado."}, status=404)
        
        if request.method == 'PATCH':
            serializer = FullUserProfileSerializer(
                instance=account,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = FullUserProfileSerializer(account)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='all-accounts')
    def all_accounts(self, request):
        accounts = Account.objects.select_related('owner__user').exclude(owner__user=request.user)
        
        serializer = AccountReadSerializer(accounts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='deposit')
    def deposit(self, request):
        idempotency_key = request.headers.get('idempotency_key')

        if idempotency_key and Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            return Response({"detail": "Transação com essa chave de idempotência já existe."}, status=400)

        account = self.get_queryset().first()
        if not account:
            return Response({"detail": "Conta não encontrada."}, status=404)
        
        serializer = DepositTransactionSerializer(data=request.data, context={'account': account, 'idempotency_key': idempotency_key})
        serializer.is_valid(raise_exception=True)
        deposit = serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
                
           