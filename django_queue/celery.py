import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'django_queue.settings')

app = Celery('django_queue')
app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()