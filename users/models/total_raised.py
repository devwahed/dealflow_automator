import uuid

from django.db import models

from users.models.ownership import OwnershipType


class TotalRaised(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ownership_type = models.ForeignKey(OwnershipType, on_delete=models.CASCADE)
    max_raised = models.BigIntegerField()
    tier = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.ownership_type} - ${self.max_raised} (Tier {self.tier})"
