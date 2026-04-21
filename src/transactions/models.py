import uuid
from django.db import models
from accounts.models import Client
from django.db.models import Q, CheckConstraint 

class TransferType(models.TextChoices):
    PIX = 'PIX', 'Pix'
    TED = 'TED', 'Transferência Eletrônica Disponível'
    DOC = 'DOC', 'Documento de Ordem de Crédito'

class StatusTransfer(models.TextChoices):
    PENDING = 'PENDING', 'Pendente'
    COMPLETED = 'COMPLETED', 'Concluído'
    FAILED = 'FAILED', 'Falhou'


class Transaction(models.Model):
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    from_account =  models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='transfer_send'
    )
    
    to_account =  models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='transfer_received'
    )
    
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    
    transfer_type = models.CharField(choices=TransferType, max_length=12)

    transfer_status = models.CharField(choices=StatusTransfer, default=StatusTransfer.PENDING, max_length=12)

    idempotency_key = models.UUIDField(unique=True, null=True, blank=True)

    transfer_created = models.DateTimeField(auto_now_add=True) # auto_now_add=True para definir a data de criação e não permitir alterações posteriores
    transfer_updated = models.DateTimeField(auto_now=True) # auto_now=True para atualizar a data sempre que o registro for salvo
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="%(app_label)s_%(class)s_transaction_amount_must_be_positive"
            )
        ]

        