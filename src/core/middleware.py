from django.http import HttpResponseForbidden
from ratelimit.utils import is_ratelimited
from .models import BlacklistedIP

class FirewallMiddleware:
    """
    Middleware de segurança global para o Core Banking.
    Detecta excesso de requisições e bane IPs automaticamente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        if BlacklistedIP.objects.filter(ip_address=ip, is_active=True).exists():
            return HttpResponseForbidden("Access Denied: Security violation detected for this IP.")

        is_limited = is_ratelimited(
            request, 
            key='ip', 
            rate='50/m', 
            group='core_global', 
            increment=True
        )

        if is_limited:
            BlacklistedIP.objects.get_or_create(
                ip_address=ip,
                defaults={
                    'reason': 'Automated block: Exceeded rate limit of 50 req/min (Potential DoS/Brute-force)'
                }
            )
            return HttpResponseForbidden("Too many requests. Your IP has been blacklisted for security reasons.")

        return self.get_response(request)