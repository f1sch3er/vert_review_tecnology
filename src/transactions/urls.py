from django.urls import include, path
from rest_framework.routers import DefaultRouter

from transactions.views.transactions_view import TransactionsView

router = DefaultRouter()

router.register(r'', TransactionsView, basename='transactions')

urlpatterns = [
    path('', include(router.urls)),
]