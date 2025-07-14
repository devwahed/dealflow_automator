import uuid

from django.db import models

from users.models.user import User


class FundraiseYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tier = models.PositiveSmallIntegerField(unique=True)
    max_year = models.PositiveIntegerField()

    def __str__(self):
        return f"Tier {self.tier} - Max Year {self.max_year}"
