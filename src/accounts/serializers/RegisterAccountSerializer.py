from django.contrib.auth import authenticate
from rest_framework import  serializers
from accounts.models import User
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

class AccountLoginSerializer(serializers.ModelSerializer):
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

        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if not user:
            raise serializers.ValidationError("E-mail ou senha incorretos.")

        else:
            raise serializers.ValidationError("E-mail e senha são obrigatórios.")
        
        
        attrs['user'] = user
        return attrs