from django.contrib import admin

from users.models.user import User
from users.models.user_configuration import UserConfiguration

admin.site.register(User)
admin.site.register(UserConfiguration)
