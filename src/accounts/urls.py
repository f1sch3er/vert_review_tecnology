from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views.accounts import AuthViewSet, ClientDetailViewset, AddressViewSet, ClientViewSet, RegisterAccountViewSet

router = DefaultRouter()

router.register(r'register', RegisterAccountViewSet, basename='register-account')
router.register(r'client', ClientViewSet, basename='create-client')
router.register(r'address', AddressViewSet, basename='create-address')
router.register(r'auth', AuthViewSet, basename='login-account')
router.register(r'details', ClientDetailViewset, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]