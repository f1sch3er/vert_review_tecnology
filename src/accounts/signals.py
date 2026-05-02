# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Client, Account

@receiver(post_save, sender=Client)
def create_client_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(owner=instance)