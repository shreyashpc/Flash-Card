from application.workers import celery
from datetime import datetime
from flask import current_app as app

from celery.schedules import crontab
print("crontab ", crontab)

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, print_current_time_job.s(), name='add every 10')

@celery.task()
def just_say_hello(name):
    print("INSIDE TASK")
    print("Hello {}".format(name))
    return("Hello {}".format(name))


@celery.task()
def print_current_time_job():
    print("START")
    now = datetime.now()
    print("now in task = ", now)
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    print("COMPLETE")
    return dt_string