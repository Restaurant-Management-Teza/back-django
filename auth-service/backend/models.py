# backend/models.py
from django.conf import settings
from django.db import models

class WaiterProfile(models.Model):
    """
    One-to-one with auth.User, only for waiters, stores zone number.
    """
    user  = models.OneToOneField(settings.AUTH_USER_MODEL,
                                 on_delete=models.CASCADE,
                                 related_name="waiter_profile")
    zone  = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} – zone {self.zone}"