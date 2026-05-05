
import logging

from transactions.models import Transaction
from transactions.serializers.transactions_serializer import RecentActivitySerializer, TransactionKafkaSerializer, TransactionsSerializer
from rest_framework import generics, mixins, viewsets, permissions as permission, status
from rest_framework.response import Response
from django.db import transaction as db_transaction
from rest_framework.permissions import IsAuthenticated
from transactions.services.transaction_producer import TransactionProducer
from django.db.models import Q

class TransactionsView(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionsSerializer
    permission_classes = [permission.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        idempotency_key = request.headers.get('idempotency_key') 

        if not idempotency_key:
            return Response(
                {'error': 'O cabeçalho idempotency_key é obrigatório.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_transaction = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transaction:
            serializer = self.get_serializer(existing_transaction)
            return Response(serializer.data, status=status.HTTP_200_OK)


        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with db_transaction.atomic():
                self.perform_create(serializer, idempotency_key)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, idempotency_key):
        transaction_obj = serializer.save(idempotency_key=idempotency_key)
        
        try:
            kafka_serializer = TransactionKafkaSerializer(transaction_obj)
            payload = kafka_serializer.data

            TransactionProducer.send_transaction(payload)
            
            print(f"Payload enviado para a fila")
            print(f"Tipo do payload: {type(payload)}")
        except Exception as e:
            logging.error(f"Erro ao serializar mensagem para Kafka: {e}")

        
class RecentActivityListAPIView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RecentActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_account = getattr(user, 'account', None)
        print(f"DEBUG: Usuário {user} | Conta: {user_account}") 

        
        if not user_account:
            return Transaction.objects.none()

        return Transaction.objects.filter(
            Q(from_account=user_account) | Q(to_account=user_account)
        ).order_by('-created_at')