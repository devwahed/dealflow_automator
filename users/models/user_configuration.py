import uuid

from django.db import models

from users.models.user import User


class UserConfiguration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuration')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    founding_year = models.ForeignKey('FoundingYear', on_delete=models.CASCADE)
    fte_count = models.ForeignKey('FTECount', on_delete=models.CASCADE)
    fundraise_year = models.ForeignKey('FundraiseYear', on_delete=models.CASCADE)
    ownership_type = models.ForeignKey('OwnershipType', on_delete=models.CASCADE)
    total_raised = models.ForeignKey('TotalRaised', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Configuration for {self.user.email}"
