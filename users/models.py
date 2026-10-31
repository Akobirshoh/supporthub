from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    CLIENT = "client", "Mijoz"
    OPERATOR = "operator", "Operator"
    ADMIN = "admin", "Admin"


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_operator(self):
        return self.role == Role.OPERATOR

    @property
    def is_client(self):
        return self.role == Role.CLIENT

    def __str__(self):
        return f"{self.username} ({self.role})"
