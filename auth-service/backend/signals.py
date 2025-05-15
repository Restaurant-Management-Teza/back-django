# backend/signals.py
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import WaiterProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_waiter_profile(sender, instance, created, **kwargs):
    """
    Whenever a new user is saved in WAITER group → ensure profile exists.
    """
    if not created:
        return

    if instance.groups.filter(name="WAITER").exists():
        WaiterProfile.objects.create(user=instance)