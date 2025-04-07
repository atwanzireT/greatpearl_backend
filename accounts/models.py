from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    # Fix related_name clashes
    groups = models.ManyToManyField(Group, related_name="customer_users", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customer_user_permissions", blank=True)

    def __str__(self):
        return self.username
