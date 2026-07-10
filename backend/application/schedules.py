from celery.schedules import crontab

beat_schedule = {
    'create_user_every_minute': {
        'task': 'print_hello',
        'schedule': crontab(minute='*/1')  # Run every minute
    }
}
