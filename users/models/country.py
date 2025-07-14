import uuid

from django.db import models

from users.models.user import User


class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    tier = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name
