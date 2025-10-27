import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
app = Celery('marketplace')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'replenish-everyday': {
        'task': 'apps.products.tasks.replenish_stock_minimum',
        'schedule': crontab(hour=0, minute=0),
        'args': (10,),
    },
}

app.conf.timezone = 'America/Fortaleza'