from django.db import models

class BlacklistedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255, default="Excessive requests / Rate limit exceeded")
    blocked_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Blacklisted IP"
        verbose_name_plural = "Blacklisted IPs"

    def __str__(self):
        return f"{self.ip_address} (Blocked: {self.blocked_at.strftime('%Y-%m-%d %H:%M')})"