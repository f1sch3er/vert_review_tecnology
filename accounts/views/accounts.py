# accounts/views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from accounts.serializers.RegisterAccountSerializer import RegisterAccountSerializer

User = get_user_model()

class RegisterAccountViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]


class AccountLoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): 
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [AllowAny]



class AccountViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterAccountSerializer
    permission_classes = [IsAuthenticated]