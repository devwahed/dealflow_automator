import uuid

from django.db import models

from users.models.ownership import OwnershipType
from users.models.user import User


class FTECount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ownership_type = models.ForeignKey(OwnershipType, on_delete=models.CASCADE)
    min_count = models.PositiveIntegerField()
    max_count = models.PositiveIntegerField()
    tier = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.ownership_type.name} (Tier {self.tier})"
