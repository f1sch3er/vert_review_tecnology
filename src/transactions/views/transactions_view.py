from django.shortcuts import render
from transactions.models import StatusTransfer, Transaction
from transactions.serializers.transactions_serializer import TransactionsSerializer
from rest_framework import viewsets, permissions as permission, response as Response, status as status

from transactions.services.transaction_producer import TransactionProducer

class TransactionsView(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionsSerializer
    permission_classes = [permission.IsAuthenticated]  


    def create(self, request, *args, **kwargs):
        
        idempotency_key = request.headers.get('idempotency_key')

        if not idempotency_key:
            return Response({'error': 'O cabeçalho idempotency_key é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_transaction = Transaction.objects.filter(idempotency_key=idempotency_key).first()

        if existing_transaction:
            serializer = self.get_serializer(existing_transaction)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        
        idempotency_key = self.request.headers.get('idempotency_key')

        transaction = serializer.save(idempotency_key=idempotency_key)
        
        payload = {
            'transaction_id': str(transaction.id),
            'from_account': transaction.from_account.account_number,
            'to_account': transaction.to_account.account_number,
            'amount': str(transaction.amount),
            'transfer_type': transaction.transfer_type,
            'idempotency_key': str(transaction.idempotency_key),
            'status': StatusTransfer.PENDING,
        }


        TransactionProducer.send_transaction(payload)
        


        


