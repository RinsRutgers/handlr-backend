import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotshot.config.local')

app = Celery('spotshot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
