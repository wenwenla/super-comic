from app import create_app, celery

flask_app = create_app()
flask_app.app_context().push()


'''
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls reverse_messages every 10 seconds.
    sender.add_periodic_task(10.0, reverse_messages, name='reverse every 10')

    # Calls log('Logging Stuff') every 30 seconds
    sender.add_periodic_task(30.0, log.s(('Logging Stuff')), name='Log every 30')

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        log.s('Monday morning log!'),
    )
'''

'''
celery -A celery_worker:celery worker --loglevel=INFO --pool=solo
'''
