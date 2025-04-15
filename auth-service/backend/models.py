# models.py
from django.db import models

class UserType(models.TextChoices):
    MANAGER = 'MANAGER', 'Manager'
    CUSTOMER = 'CUSTOMER', 'Customer'
    WAITER = 'WAITER', 'Waiter'

# models.py
class SimpleUserManager(models.Manager):
    def create_user(self, email, username, password=None, user_type=UserType.CUSTOMER, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        # Basic user creation
        user = self.model(
            email=email,
            username=username,
            user_type=user_type,
            **extra_fields
        )
        user.password = password  # or hash it if you prefer
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, user_type=UserType.MANAGER, **extra_fields):
        """For demonstration, let's treat 'MANAGER' as 'superuser'."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        # you can also store is_superuser if you want a custom logic
        return self.create_user(email, username, password, user_type, **extra_fields)

class DefaultUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, blank=True)  # or hashed if you prefer
    full_name = models.CharField(max_length=255, blank=True)

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = SimpleUserManager()

    def __str__(self):
        return f"{self.username} ({self.email})"