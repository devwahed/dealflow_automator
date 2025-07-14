from django.contrib import admin
from users.models.user import User
from users.models.country import Country
from users.models.total_raised import TotalRaised
from users.models.fundraise_year import FundraiseYear
from users.models.founding_year import FoundingYear
from users.models.fte_count import FTECount
# Register your models here.

admin.site.register(User)
admin.site.register(Country)
admin.site.register(TotalRaised)
admin.site.register(FundraiseYear)
admin.site.register(FoundingYear)
admin.site.register(FTECount)


