import uuid
from django.core.validators import MinValueValidator
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, UserManager
from decimal import Decimal
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório')
        
        email = self.normalize_email(email)
        
        extra_fields.pop('username', None) 
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        return self.create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  
    is_superuser = models.BooleanField(default=False) 

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    
    @property
    def is_any_admin(self):
        return any([self.is_admin, self.is_staff, self.is_superuser])
    
class Account(models.Model):
    owner = models.ForeignKey('Client', on_delete=models.CASCADE, related_name="accounts")
    account_number = models.CharField(max_length=36, unique=True, default=uuid.uuid4, editable=False)
    balance = models.DecimalField(
        max_digits=19, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    blocked_balance = models.DecimalField(
        max_digits=19, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def available_balance(self):
        return self.balance - self.blocked_balance
    
    class Meta: 
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance__gte=0), 
                name="%(app_label)s_%(class)s_balance_not_negative"
            ),
            models.CheckConstraint(
                check=models.Q(blocked_balance__gte=0), 
                name="%(app_label)s_%(class)s_blocked_balance_not_negative"
            ),
            models.CheckConstraint(
                check=models.Q(balance__gte=models.F('blocked_balance')),
                name="%(app_label)s_%(class)s_blocked_less_than_total"
            )
        ]

    def __str__(self):
        # Corrigido para acessar o email através do relacionamento Client -> User
        return f"Conta {self.account_number} - {self.owner.user.email}"

class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True, related_name='client_address')

    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()
    document_number = models.CharField(max_length=50, unique=True)
    document_type = models.CharField(max_length=15, choices=DocumentType)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return self.user.email
    
