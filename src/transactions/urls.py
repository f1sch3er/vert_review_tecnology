from django.urls import include, path
from rest_framework.routers import DefaultRouter

from transactions.views.transactions_view import RecentActivityListAPIView, TransactionsView

router = DefaultRouter()

router = DefaultRouter()

router.register(r'recent-activity', RecentActivityListAPIView, basename='recent-activity')
router.register(r'', TransactionsView, basename='transactions')

urlpatterns = [
    path('', include(router.urls)),
]