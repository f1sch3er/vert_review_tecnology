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
    
    from_account = serializers.SlugRelatedField(
        slug_field='account_number',
        queryset=Account.objects.all(),
        write_only=True
    )
    to_account = serializers.SlugRelatedField(
        slug_field='account_number',
        queryset=Account.objects.all(),
        write_only=True
    )

    from_account_number = serializers.CharField(source='from_account.account_number', read_only=True)
    to_account_number = serializers.CharField(source='to_account.account_number', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'from_account', 'to_account', 
            'from_account_number', 'to_account_number',
            'amount', 'transfer_type', 'transfer_status', 'transfer_created',
        ]

    def validate(self, attrs):
        from_acc = attrs.get('from_account')
        to_acc = attrs.get('to_account')
        amount = attrs.get('amount')

        if from_acc == to_acc:
            raise serializers.ValidationError("A conta de origem e destino não podem ser iguais.")

        if amount <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")

        user = self.context['request'].user
        if from_acc.owner.user != user:
            raise serializers.ValidationError("Você só pode transferir de uma conta que lhe pertence.")

        return attrs


class TransactionDetailSerializer(serializers.ModelSerializer):
    from_account_number = serializers.ReadOnlyField(source='from_account.account_number')
    from_account_name = serializers.ReadOnlyField(source='from_account.owner.user.get_full_name')
    from_account_email = serializers.ReadOnlyField(source='from_account.owner.user.email')
    
    to_account_number = serializers.ReadOnlyField(source='to_account.account_number')
    to_account_name = serializers.ReadOnlyField(source='to_account.owner.user.get_full_name')
    to_account_email = serializers.ReadOnlyField(source='to_account.owner.user.email')
    
    type_display = serializers.CharField(source='get_transfer_type_display', read_only=True)
    status_display = serializers.CharField(source='get_transfer_status_display', read_only=True)
    date_formatted = serializers.DateTimeField(source='transfer_created', format="%d/%m/%Y %H:%M:%S")
    
    direction = serializers.SerializerMethodField()
    relevant_balance_after = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 
            'amount', 
            'direction', 
            'type_display', 
            'status_display',
            'external_code',
            'idempotency_key',
            'date_formatted',
            'transfer_created',
            'transfer_updated',
            
            'from_account_name', 
            'from_account_number',
            'from_account_email',
            
            'to_account_name', 
            'to_account_number',
            'to_account_email',
            
            'relevant_balance_after', 
            'from_account_balance_after',
            'to_account_balance_after',
        ]

    def get_direction(self, obj):
        user = self.context['request'].user
        if obj.from_account and obj.from_account.owner.user == user:
            return 'OUT'
        return 'IN'

    def get_relevant_balance_after(self, obj):
        """
        Retorna o saldo que faz sentido para o usuário logado visualizar.
        Se ele enviou, mostra o from_account_balance_after.
        Se ele recebeu, mostra o to_account_balance_after.
        """
        user = self.context['request'].user
        if obj.from_account and obj.from_account.owner.user == user:
            return obj.from_account_balance_after
        if obj.to_account and obj.to_account.owner.user == user:
            return obj.to_account_balance_after
        return None
    
class RecentActivitySerializer(serializers.ModelSerializer):
    type_display = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    date_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'type_display', 'direction', 'amount', 'date_formatted', 'transfer_status']

    def get_type_display(self, obj):
        user_account = self.context.get('user_account')

        if obj.transfer_type == 'DEPOSIT':
            return "Depósito Recebido"
        
        if obj.from_account == user_account:
            return "Transferência Enviada"
        
        return "Transferência Recebida"

    def get_direction(self, obj):
        user = self.context['request'].user
        user_account = getattr(user, 'account', None)
        
        if not user_account:
            return "OUT" 

        if obj.to_account == user_account:
            return "IN" 
        return "OUT"    

    def get_date_formatted(self, obj):
        if obj.transfer_created:
            return obj.transfer_created.strftime("%d/%m/%Y")
        return ""
        
class DepositKafkaSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(source='id')
    from_account = serializers.SerializerMethodField()
    to_account = serializers.CharField(source='to_account.account_number')
    status = serializers.CharField(source='transfer_status')

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'from_account', 'to_account', 
            'amount', 'transfer_type', 'idempotency_key', 'status'
        ]

    def get_from_account(self, obj):
        return None
    
class TransactionKafkaSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(source='id')
    from_account = serializers.CharField(source='from_account.account_number', allow_null=True)
    to_account = serializers.CharField(source='to_account.account_number')
    status = serializers.CharField(source='transfer_status')

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'from_account', 'to_account', 
            'amount', 'transfer_type', 'idempotency_key', 'status'
        ]