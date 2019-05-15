# coding:utf-8


from celery import Celery, platforms

platforms.C_FORCE_ROOT = True
# from ihome.tasks_pay import config

app = Celery("paydex")

# app.config_from_object(config)
app.config_from_object("app.tasks_pay.config")

# 让celery自己找到任务
app.autodiscover_tasks(["app.tasks_time.time_task"])

# "app.tasks_pay.pay_tasks.pay_stellar",
# "app.tasks_pay.pay_tasks.time_task",
# "app.tasks_pay.pay_tasks.pay_requests",
