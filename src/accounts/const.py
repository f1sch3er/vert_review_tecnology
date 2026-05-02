from django.db import models

class DocumentType(models.TextChoices):
    CPF = 'CPF', 'Cpf'
    CNPJ = 'CNPJ', 'Cnpj'

class TransferType(models.TextChoices):
    PIX = 'PIX', 'Pix'
    TED = 'TED', 'Transferência Eletrônica Disponível'
    DOC = 'DOC', 'Documento de Ordem de Crédito'
    DEPOSIT = 'DEPOSIT', 'Depósito'

class StatusTransfer(models.TextChoices):
    PENDING = 'PENDING', 'Pendente'
    COMPLETED = 'COMPLETED', 'Concluído'
    FAILED = 'FAILED', 'Falhou'