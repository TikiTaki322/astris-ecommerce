import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doom_market.settings")

app = Celery("doom_market")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()