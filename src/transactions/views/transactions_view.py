from django.shortcuts import render
from accounts.models import Account
from transactions.models import StatusTransfer, Transaction
from transactions.serializers.transactions_serializer import TransactionKafkaSerializer, TransactionsSerializer
from rest_framework import viewsets, permissions as permission, status
from rest_framework.response import Response


class TransactionsView(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionsSerializer
    permission_classes = [permission.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        idempotency_key = request.headers.get('idempotency_key') # Headers costumam usar hífen

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
        
        kafka_serializer = TransactionKafkaSerializer(transaction_obj)
        payload = kafka_serializer.data
        
        print(f"Payload enviado para Kafka: {payload}")        


        


