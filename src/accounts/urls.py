from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views.accounts import AuthViewSet, AccountMeViewSet, ClientViewSet, NewUserViewSet

router = DefaultRouter()

router.register(r'users', NewUserViewSet, basename='users')
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'accounts', AccountMeViewSet, basename='accounts')

urlpatterns = [
    path('', include(router.urls)),
]