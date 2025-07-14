import uuid

from django.db import models

from users.models.user import User


class UserConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuration')
    configuration_json = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Configuration for {self.user.email}"
