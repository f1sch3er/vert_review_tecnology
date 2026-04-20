from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views.accounts import AccountLoginViewSet, AccountDetailViewset, CreateAddressViewSet, CreateClientViewSet, RegisterAccountViewSet

router = DefaultRouter()

router.register(r'register', RegisterAccountViewSet, basename='register-account')
router.register(r'client', CreateClientViewSet, basename='create-client')
router.register(r'address', CreateAddressViewSet, basename='create-address')
router.register(r'auth', AccountLoginViewSet, basename='login-account')
router.register(r'details', AccountDetailViewset, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]