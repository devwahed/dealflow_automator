from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from users.views import configuration
from users.views.configuration import submit_configuration, get_configuration
from users.views.task_status import task_status
from users.views.upload_csv import UploadAndTierView

urlpatterns = [
    path('', configuration, name='create_user_configuration'),
    path("submit-configuration/", submit_configuration, name="submit_configuration"),
    path("get-configuration/", get_configuration, name="get-configuration"),
    path("upload-csv/", UploadAndTierView.as_view(), name="upload_csv"),
    path('task-status/<str:task_id>/', task_status, name='task_status'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
