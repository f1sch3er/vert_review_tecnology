
import logging

from accounts.models import Account
from core.utils import PaginationClass
from transactions.models import Transaction
from transactions.serializers.transactions_serializer import RecentActivitySerializer, TransactionDetailSerializer, TransactionKafkaSerializer, TransactionsSerializer
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
        from_account = serializer.validated_data.get("from_account")
        amount = serializer.validated_data.get("amount")

        if from_account and amount:
            if from_account.balance < amount:
                raise Exception("Saldo insuficiente")
            
        transaction_obj = serializer.save(idempotency_key=idempotency_key)
        
        try:
            kafka_serializer = TransactionKafkaSerializer(transaction_obj)
            payload = kafka_serializer.data

            TransactionProducer.send_transaction(payload)
            
            print(f"Payload enviado para a fila")
            print(f"Tipo do payload: {type(payload)}")
        except Exception as e:
            logging.error(f"Erro ao serializar mensagem para Kafka: {e}")

        
class RecentActivityViewSet(mixins.ListModelMixin, 
                            mixins.RetrieveModelMixin, 
                            viewsets.GenericViewSet):
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    pagination_class = PaginationClass

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(
            Q(from_account__owner__user=user) |
            Q(to_account__owner__user=user)
        ).select_related(
            'from_account__owner__user',
            'to_account__owner__user'
        ).order_by('-transfer_created').distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        return RecentActivitySerializer