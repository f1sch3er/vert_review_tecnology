from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.db import transaction
from rest_framework import serializers
from rest_framework.reverse import reverse
from accounts.models import Account, Address, Client, User
from django.shortcuts import get_object_or_404


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
            user_data = data.copy()
            user_data.pop("password_confirm", None)

            user = User(
                email=data.get("email"),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
            )
            validate_password(data['password'], user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)

class UserRegistrationResponseSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')
    links = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'links')

    def get_links(self, obj):
        request = self.context.get('request')
        return {
            "login": {
                "rel": "authenticate",
                "href": "/api/token/",
                "method": "POST",
                "description": "Obter token JWT para acessar a conta"
            },
            "complete_profile": {
                "rel": "complete_registration",
                "href": "/api/clients/",
                "method": "POST",
                "description": "Enviar dados complementares para abertura de conta"
            }
        }
    
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
        user = validated_data.pop('user') 

        with transaction.atomic():
            address = Address.objects.create(**address_data)
            client = Client.objects.create(
                user=user,
                address=address,
                **validated_data
            )

        return client 

class ClientSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='user.get_full_name')
    email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Client
        fields = ['id', 'full_name', 'email']

class AccountReadSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.user.first_name')

    class Meta:
        model = Account
        fields = ['id', 'owner', 'owner_name', 'account_number', 'balance', 'blocked_balance', 'available_balance', 'created_at', 'updated_at'] 

    def get_owner_name(self, obj):
        full_name = obj.owner.user.get_full_name()
        return full_name if full_name else obj.owner.user.username
    
class CreateAccountSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Account
        fields = '__all__'

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        target_user_id = validated_data.pop('user_id', None)

        if user.is_any_admin and target_user_id:
            target_user = get_object_or_404(User, id=target_user_id)
        else:
            target_user = user


        client = getattr(target_user, "client", None)

        if not client:
            raise serializers.ValidationError("Usuário não possui client.")

        account = Account.objects.create(owner=client)
        return account

class UpsertUserProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    phone_number = serializers.CharField(required=False)
    document_type = serializers.CharField(required=False)
    document_number = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)

    address = serializers.DictField(required=False)

    def update(self, instance, validated_data):
        user = instance.owner.user
        owner = instance.owner

        # user
        for field in ['first_name', 'last_name', 'email']:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        # client (owner)
        for field in ['phone_number', 'document_type', 'document_number', 'birth_date']:
            if field in validated_data:
                setattr(owner, field, validated_data[field])
        owner.save()

        # address
        address_data = validated_data.get('address')
        if address_data:
            address = getattr(owner, 'address', None)

            if address:
                for attr, value in address_data.items():
                    setattr(address, attr, value)
                address.save()
            else:
                address = Address.objects.create(**address_data)
                owner.address = address
                owner.save()

        return instance
        
class FullUserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='owner.user.first_name')
    last_name = serializers.CharField(source='owner.user.last_name')
    email = serializers.EmailField(source='owner.user.email')
    
    phone = serializers.CharField(source='owner.phone_number')
    document_type = serializers.CharField(source='owner.document_type')
    document_number = serializers.CharField(source='owner.document_number')
    birth_date = serializers.DateField(source='owner.birth_date')
    
    address = AddressSerializer(source='owner.address')

    class Meta:
        model = Account
        fields = (
            'first_name', 'last_name', 'email', 
            'phone', 'document_type', 'document_number', 'birth_date',
            'address'
        )

    
    def update(self, instance, validated_data):
        owner_data = validated_data.pop('owner', {})
        user_data = owner_data.pop('user', {})
        address_data = owner_data.pop('address', {})

        user = instance.owner.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        address = instance.owner.address
        if address:
            for attr, value in address_data.items():
                setattr(address, attr, value)
            address.save()

        owner = instance.owner
        for attr, value in owner_data.items():
            setattr(owner, attr, value)
        owner.save()

        return instance

class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserDetailSerializer()
    links = serializers.SerializerMethodField()

    def get_links(self, obj):
        request = self.context["request"]

        return {
            "self": reverse("auth-list", request=request),
            "refresh": reverse("token_refresh", request=request),
            "me": reverse("users-list", request=request),
        }
