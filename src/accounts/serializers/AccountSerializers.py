from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.db import transaction

from rest_framework import serializers

from accounts.models import Account, Address, Client, User

User = get_user_model()




class RegisterAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="Mínimo de 8 caracteres"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "As senhas não conferem."})

        try:
            user = User(**data)
            validate_password(data['password'], user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)

class AccountLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        required=True,
        allow_blank=False, 
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        print(f"Validating login for email: {email}", flush=True)

        if not email or not password:
            raise serializers.ValidationError(
                "E-mail e senha são obrigatórios."
            )

        user = authenticate(request=self.context.get('request'), email=email, password=password)

        if not user:
            raise serializers.ValidationError(
                "Credenciais inválidas. Verifique seu e-mail e senha."
            )
        
        attrs['user'] = user
        return attrs

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('street', 'city', 'state', 'zip_code')

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_any_admin')

class ClientDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Client
        fields = ('document_number', 'document_type', 'phone_number', 'birth_date', 'user', 'address')


class CreateClientSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = Client
        fields = ('phone_number', 'birth_date', 'document_number', 'document_type', 'address')

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        user = self.context['request'].user

        with transaction.atomic():
            address = Address.objects.create(**address_data)
            client = Client.objects.create(user=user, address=address, **validated_data)
            Account.objects.create(owner=client)
            
            return client
 

class AccountDetailSerializer(serializers.ModelSerializer):
    owner = ClientDetailSerializer(read_only=True)

    class Meta:
        model = Account
        fields = ('account_number', 'balance', 'available_balance', 'created_at', 'owner')

