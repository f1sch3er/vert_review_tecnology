from django.db import connections
from django.db.utils import OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated


class HealCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            "status": "healthy",
            "dependencies": {
                "database": "up",
                "storage": "up"
            }
        }

        conn = connections['default']
        try:
            conn.cursor()
        except OperationalError:
            health_status['status'] = 'unhealthy'
            health_status['dependencies']['database'] = 'down'

            http_status = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        
        return Response(health_status, status=200)