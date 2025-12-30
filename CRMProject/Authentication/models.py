from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import uuid
from datetime import timedelta

class LoginRole(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('SUPERVISOR', 'Supervisor'),
        ('AGENT', 'Agent'),
    )

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name




class LoginUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.ForeignKey(LoginRole, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    reset_token = models.CharField(max_length=64, null=True, blank=True)
    reset_token_expiry = models.DateTimeField(null=True, blank=True)

    # 🔐 Proper password setter
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save(update_fields=["password"])

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # 🔑 Generate reset token
    def generate_reset_token(self):
        self.reset_token = uuid.uuid4().hex
        self.reset_token_expiry = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=["reset_token", "reset_token_expiry"])
        return self.reset_token

    # ⏳ Token validity check
    def is_reset_token_valid(self):
        return (
            self.reset_token
            and self.reset_token_expiry
            and timezone.now() <= self.reset_token_expiry
        )

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None
        self.save(update_fields=["reset_token", "reset_token_expiry"])

    def __str__(self):
        return self.email
