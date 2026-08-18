from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'Create', 'Create'
        UPDATE = 'Update', 'Update'
        DELETE = 'Delete', 'Delete'
        LOGIN = 'Login', 'Login'
        LOGOUT = 'Logout', 'Logout'
        POST = 'Post', 'Post'
        REVERSE = 'Reverse', 'Reverse'
        CLOSE = 'Close', 'Close'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action} - {self.model_name}#{self.object_id}"
