from transactions.models import Transaction
from rest_framework import  serializers


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