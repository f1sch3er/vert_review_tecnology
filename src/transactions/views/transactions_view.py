from django.shortcuts import render
from accounts.models import Account
from transactions.models import StatusTransfer, Transaction
from transactions.serializers.transactions_serializer import TransactionKafkaSerializer, TransactionsSerializer
from rest_framework import viewsets, permissions as permission, status
from rest_framework.response import Response

from transactions.services.transaction_producer import TransactionProducer

class TransactionsView(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionsSerializer
    permission_classes = [permission.IsAuthenticated]  


    def create(self, request, *args, **kwargs):
        
        idempotency_key = request.headers.get('idempotency_key')

        if not idempotency_key:
            return Response({'error': 'O cabeçalho idempotency_key é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        self.from_account(request, *args, **kwargs)
        self.to_account(request, *args, **kwargs)
    
        existing_transaction = Transaction.objects.filter(idempotency_key=idempotency_key).first()

        if existing_transaction:
            serializer = self.get_serializer(existing_transaction)
            return Response(serializer.data, status=status.HTTP_200_OK)
        

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def from_account(self, request, *args, **kwargs):
        from_account_id = request.data.get('from_account')
        if not from_account_id:
            return Response({'error': 'O parâmetro from_account é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        account = Account.objects.filter(account_number=from_account_id).first()
        if not account:
            return Response({'error': 'Conta de origem não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        
        request.data['from_account'] = account.id
        
    def to_account(self, request, *args, **kwargs):
        to_account = request.data.get('to_account')
        if not to_account:
            return Response({'error': 'O parâmetro to_account é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        account = Account.objects.filter(account_number=to_account).first()
        if not account:
            return Response({'error': 'Conta de destino não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        
        request.data['to_account'] = account.id

    def perform_create(self, serializer):
        idempotency_key = self.request.headers.get('idempotency_key')

        transaction = serializer.save(idempotency_key=idempotency_key)
        kafka_serializer = TransactionKafkaSerializer(transaction)
        payload = kafka_serializer.data

        
        print(f"Payload a ser enviado para Kafka: {payload}", flush=True)

        TransactionProducer.send_transaction(payload)
        


        


