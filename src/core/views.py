from django.db import connections
from django.db.utils import OperationalError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from kafka import KafkaAdminClient
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings

@api_view(['GET'])
def kafka_health_check(request):
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=3000
        )
        topics = admin_client.list_topics()
        admin_client.close()
        
        return Response({
            "status": "online",
            "broker": settings.KAFKA_BOOTSTRAP_SERVERS,
            "topics": topics
        }, status=200)
    except Exception as e:
        return Response({
            "status": "offline",
            "error": str(e),
            "tried_broker": settings.KAFKA_BOOTSTRAP_SERVERS
        }, status=503)
        
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