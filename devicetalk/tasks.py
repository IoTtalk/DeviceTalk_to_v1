from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler import util
from django_apscheduler.jobstores import (
    DjangoJobStore,
    register_job,
)
from django_apscheduler.models import DjangoJobExecution

import devicetalk.service


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after our job has run.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age`
    from the database. It helps to prevent the database from filling up with
    old historical records that are no longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


# run periodic task by apscheduler
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), 'default')


def init_periodic_tasks():
    # fix error when ./manage.py migrate
    # ref: https://githubmemory.com/repo/jcass77/django-apscheduler/issues/108
    isExistTable = False
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM django_apscheduler_djangojob')
        cursor.close()
        isExistTable = True
    except Exception:
        pass

    if isExistTable:
        try:
            scheduler.start()
        except Exception:
            scheduler.shutdown()
    pass


@register_job(scheduler, 'cron', id='cleanup_routine', hour=5, minute=0, replace_existing=True, misfire_grace_time=60)  # noqa:E501
def cleanup_routine():
    """
        periodically check and delete the expired temp users,
    """
    devicetalk.service.cleanup_routine()
