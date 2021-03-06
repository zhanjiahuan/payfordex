# coding:utf-8

# 某个程序中出现的队列，在broker中不存在，则立刻创建它
CELERY_CREATE_MISSING_QUEUES = True


BROKER_URL = 'redis://root:CXsBYfis6JQYa8iV@47.52.130.34:6479/5'
CELERY_RESULT_BACKEND ='redis://root:CXsBYfis6JQYa8iV@47.52.130.34:6479/6'

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERYD_CONCURRENCY = 20  # 并发worker数
# 限制所有的任务的刷新频率
CELERY_ANNOTATIONS = {'*': {'rate_limit': '10/s'}}
# celery worker每次去redis取任务的数量，默认值就是4
CELERYD_PREFETCH_MULTIPLIER = 1
# 设置时区
CELERY_TIMEZONE = 'Asia/Shanghai'
# 启动时区设置
CELERY_ENABLE_UTC = True
CELERYD_FORCE_EXECV = True  # 非常重要,有些情况下可以防止死锁
CELERYD_MAX_TASKS_PER_CHILD = 100  # 每个worker最多执行万多少个个任务就会被销毁，可防止内存泄露
# 任务发出后，经过一段时间还未收到acknowledge（确认） , 就将任务重新交给其他worker执行
CELERY_DISABLE_RATE_LIMITS = True
# result_expires = 60 * 60 * 24  # 存储结果过期时间（默认1天）
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24  # 存储结果过期时间（默认1天）

# 创建exchange
# pay_requests_exchange = Exchange('pay_requests', type='direct')
# time_task_exchange = Exchange('time_task', type='direct')
# pay_stellar_exchange = Exchange('pay_stellar', type='direct')
# # 创建CELERY_QUEUES
# CELERY_QUEUES = (
#     Queue('default', Exchange('default'), routing_key='default'),
#     Queue('pay_requests', pay_requests_exchange, routing_key='pay_requests'),
#     Queue('time_task', time_task_exchange, routing_key='time_task'),
#     Queue('pay_stellar', pay_stellar_exchange, routing_key='pay_stellar')
# )
# # 定义默认的QUEUE, EXCHANGE和ROUTING_KEY
# CELERY_DEFAULT_QUEUE = 'pay_requests'
# CELERY_DEFAULT_EXCHANGE = 'pay_requests'
# CELERY_DEFAULT_ROUTING_KEY = 'pay_requests'
# # 定义路由
# # 示例：
# # tasks_pay.process_http_action.execute_process_action_http_requests 该函数产生的任务
# # 会发送至http_task Queue中且routing_key为http_task
# CELERY_ROUTES = (
#     {
#         'app.tasks_pay.pay_tasks.pay_requests': {
#             'queue': 'pay_requests',
#             'routing_key': 'pay_requests'
#         }
#     },
#     {
#         'app.tasks_pay.pay_tasks.time_task': {
#             'queue': 'time_task',
#             'routing_key': 'time_task'
#         }
#     },
#     {
#         'app.tasks_pay.pay_tasks.pay_stellar': {
#             'queue': 'pay_stellar',
#             'routing_key': 'pay_stellar'
#         }
#     }
#
# )
# # 导入任务所在文件
# CELERY_IMPORTS = [
#     "app.tasks_pay.pay.tasks_pay",  # 导入py文件
#     "app.tasks_pay.time_task.tasks_pay",
#     "app.tasks_pay.stellar_task.tasks_pay"
# ]
# CELERYBEAT_SCHEDULE = {
#     "requests_steallar_false_over_time": {
#         "task":"app.timing_task.timing_tasks.requests_steallar_false_over_time",  #执行的函数
#         'schedule': timedelta(seconds=10),
#         # "schedule": crontab(minute="*/1"),   # every minute 每分钟执行
#         # "args": ()
#     },
#
#     "requests_stellar_true_over_time":{
#         "task": "app.timing_task.timing_tasks.requests_stellar_true_over_time",
#         'schedule': timedelta(seconds=10),
        # "schedule": crontab(minute="*/1"),
        # "args": ()
    # },
    # "requests_php_over_time": {
    #     "task": "app.timing_task.timing_tasks.requests_php_over_time",
    #     "schedule": crontab(minute="*/1"),
    #     # "args": ()
    # },

# }