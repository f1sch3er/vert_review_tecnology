import uuid
from django.db import models

from accounts.const import StatusTransfer, TransferType

class Transaction(models.Model):
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    from_account =  models.ForeignKey(
        'accounts.Account',
        on_delete=models.PROTECT,
        null=True,   
        blank=True,  
        related_name='transfer_send'
    )
    
    to_account =  models.ForeignKey(
        'accounts.Account',
        on_delete=models.PROTECT,
        related_name='transfer_received'
    )
    
    idempotency_key = models.UUIDField(unique=True, null=True, blank=True)
    external_code = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    transfer_type = models.CharField(choices=TransferType, max_length=12)
    transfer_status = models.CharField(choices=StatusTransfer, default=StatusTransfer.PENDING, max_length=12)
    from_account_balance_after = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    to_account_balance_after = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    transfer_created = models.DateTimeField(auto_now_add=True) 
    transfer_updated = models.DateTimeField(auto_now=True) 
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="%(app_label)s_%(class)s_transaction_amount_must_be_positive"
            )
        ]

        

class BacenMessages(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='logs')
    request_payload = models.JSONField()
    response_payload = models.JSONField()
    endpoint = models.CharField(max_length=255)
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)