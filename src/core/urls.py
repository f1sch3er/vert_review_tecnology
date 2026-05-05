
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import include, path

from core.views import HealCheckView, kafka_health_check


urlpatterns = [
    path('', HealCheckView.as_view()),
    path('api/health/kafka/', kafka_health_check, name='kafka-health'),
    path('api/admin/', admin.site.urls),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('accounts.urls')),
    path('api/transactions/', include('transactions.urls')),
]
