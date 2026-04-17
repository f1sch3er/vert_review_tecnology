from django.db import models

from django.db import models
import uuid
from accounts.models import Client

from django.db import models

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
    
    to_account =  models.UUIDField(
        Client,
        on_delete=models.PROTECT,
        related_name='transfer_received'
    )
    
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    
    transfer_type = models.CharField(choices=TransferType.TYPE_TRANSFER)

    transfer_status = models.CharField(choices=StatusTransfer.STATUS_TRANSFER, default=StatusTransfer.STATUS_TRANSFER.PENDING)

    idempotency_key = models.UUIDField(unique=True, null=True, blank=True)

    transfer_created = models.DateTimeField(auto_now=True)

