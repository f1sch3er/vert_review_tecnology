from decimal import Decimal

from accounts.const import StatusTransfer, TransferType
from accounts.models import Account
from transactions.models import Transaction
from rest_framework import  serializers
from django.db import transaction

from transactions.services.transaction_producer import TransactionProducer

    
class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=19, decimal_places=2, min_value=0.01)
    external_code = serializers.CharField(max_length=255, required=False)
    idempotency_key = serializers.UUIDField(required=False)
    
class DepositTransactionSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=19, 
        decimal_places=2, 
        min_value=Decimal('0.01') 
    )
    external_code = serializers.CharField(max_length=255, required=False)
    idempotency_key = serializers.UUIDField(required=False)
    
    class Meta:
        model = Transaction
        fields = ['amount', 'idempotency_key', 'external_code']
    
    def create(self, validated_data):
        account = self.context['account']
        amount = validated_data['amount']

        with transaction.atomic():
            account = Account.objects.select_for_update().get(pk=account.pk)
            
            account.balance += amount
            account.save()

            validated_data.pop('amount', None)
            
            tx = Transaction.objects.create(
                to_account=account,
                from_account=None,
                amount=amount,
                transfer_type=TransferType.DEPOSIT,
                transfer_status=StatusTransfer.COMPLETED,
                to_account_balance_after=account.balance,
                **validated_data 
            )

            payload = {
                "transaction_id": str(tx.id),
                "amount": float(tx.amount),
                "to_account": account.account_number,
                "idempotency_key": str(tx.idempotency_key),
                "status": tx.transfer_status
            }
            
            TransactionProducer.send_transaction(payload)
            
            return tx  
            
class TransactionsSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    
    from_account_number = serializers.CharField(source='from_account.account_number', read_only=True)
    to_account_number = serializers.CharField(source='to_account.account_number', read_only=True)

    transfer_created = serializers.DateTimeField(read_only=True)
    transfer_status = serializers.CharField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'from_account_number',
            'to_account_number',
            'amount',
            'transfer_type',
            'transfer_status',
            'transfer_created',
        ]


    def validate(self, attrs):
        from_account = attrs.get('from_account')
        to_account = attrs.get('to_account')
        amount = attrs.get('amount')

        if from_account == to_account:
            raise serializers.ValidationError({'to_account': 'A conta de destino deve ser diferente da conta de origem.'})
        
        if amount and amount <= 0:
            raise serializers.ValidationError({'amount': 'O valor da transferência deve ser maior que zero.'})
        
        return attrs

class TransactionKafkaSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(source='id')
    from_account = serializers.CharField(source='from_account.account_number')
    to_account = serializers.CharField(source='to_account.account_number')
    status = serializers.CharField(source='transfer_status')

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'from_account', 'to_account', 
            'amount', 'transfer_type', 'idempotency_key', 'status'
        ]