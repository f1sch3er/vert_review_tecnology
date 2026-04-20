from xmlrpc import client

from django.contrib.auth import authenticate
from rest_framework import  serializers
from accounts.models import Address, Client, User
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        min_length=8
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
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
    

class CreateClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            'phone_number',
            'birth_date',
            'document_number',
            'document_type'
        )

    def create(self, validated_data):
        user = self.context["request"].user

        if not user.is_authenticated:
            raise serializers.ValidationError("Usuário não autenticado.")
        
        if Client.objects.filter(user=user).exists():
            raise serializers.ValidationError("O usuário já possui um perfil de cliente.")
        
        
        return Client.objects.create(user=user, **validated_data)

        
class CreateAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('street', 'city', 'state', 'zip_code')
    
    def create(self, validated_data):
        user = self.context['request'].user
        client = getattr(user, 'client_profile', None)

        if not client:
            raise serializers.ValidationError("Erro interno: O usuário não possui um perfil de cliente associado.")
        
        address = Address.objects.create(**validated_data)

        client.address = address
        client.save()

        return address

class DetailUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True, source='user.email')
    first_name = serializers.CharField(read_only=True, source='user.first_name')
    last_name = serializers.CharField(read_only=True, source='user.last_name')

    class Meta:
        model = Client
        fields = (
            'email', 
            'first_name', 
            'last_name', 
            'address'
        )


