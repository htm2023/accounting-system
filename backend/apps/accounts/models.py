from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'Admin', 'Admin'
        ACCOUNTANT = 'Accountant', 'Accountant'
        VIEWER = 'Viewer', 'Viewer'

    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_accountant(self):
        return self.role in [self.Role.ADMIN, self.Role.ACCOUNTANT]
