from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models



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


class Client(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.OneToOneField(Address, on_delete=models.CASCADE)

    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()
    document_number = models.CharField(max_length=50)
    document_type = models.CharField(max_length=15, choices=DOCUMENT_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)





    def __str__(self):
        return self.user.email