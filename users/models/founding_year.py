import uuid

from django.db import models


class FoundingYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tier = models.PositiveSmallIntegerField(unique=True)
    max_year = models.PositiveIntegerField()

    def __str__(self):
        return f"Tier {self.tier} - Max Year {self.max_year}"
