from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin



# MUDANDO O LOGIN DEFAULT, PARA O EMAIL E CRIANDO O MODELO DE USUÁRIO PERSONALIZADO
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128)

    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)


class DocumentType(models.TextChoices):
    CPF = 'CPF', 'Cpf'
    CNPJ = 'CNPJ', 'Cnpj'


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.OneToOneField(Address, on_delete=models.CASCADE)

    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()
    document_number = models.CharField(max_length=50)
    document_type = models.CharField(max_length=15, choices=DocumentType)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return self.user.email
    
class Account(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    account_number = models.CharField(max_length=20, unique=True, null=True, default=None)
    balance=models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta: 
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance__gte=0), 
                name="%(app_label)s_%(class)s_balance_not_negative"
            )
        ]

    def __str__(self):
        return f"Conta {self.account_number} - {self.owner.username}"