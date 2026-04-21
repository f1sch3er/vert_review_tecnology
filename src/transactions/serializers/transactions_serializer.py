from transactions.models import Transaction
from rest_framework import  serializers


class TransactionsSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    transfer_created = serializers.DateTimeField(read_only=True)
    transfer_status = serializers.CharField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'from_account',
            'to_account',
            'amount',
            'transfer_type',
            'transfer_status',
            'transfer_created',
        ]


    def validate(self, attrs):

        if self.data.get('from_account') == self.data.get('to_account'):
            raise serializers.ValidationError({'to_account': 'A conta de destino deve ser diferente da conta de origem.'})
        
        return self.data
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError({'amount': 'O valor da transferência deve ser maior que zero.'})