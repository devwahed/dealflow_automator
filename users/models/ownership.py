import uuid

from django.db import models


class OwnershipType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    tier = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name
