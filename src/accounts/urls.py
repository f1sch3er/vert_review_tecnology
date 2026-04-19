from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views.accounts import AccountLoginViewSet, AccountViewSet, RegisterAccountViewSet

router = DefaultRouter()

router.register(r'register', RegisterAccountViewSet, basename='register-account')
router.register(r'auth', AccountLoginViewSet, basename='login-account')
router.register(r'details', AccountViewSet, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]