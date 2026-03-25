"""Celery application for ProphetAI."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prophetai.settings")

app = Celery("prophetai")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
