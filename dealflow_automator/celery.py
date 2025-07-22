import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dealflow_automator.settings')

app = Celery('dealflow_automator')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
