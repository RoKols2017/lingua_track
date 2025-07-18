import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lingua_track.settings')

app = Celery('lingua_track')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() 