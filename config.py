# encoding=utf8
import os
from datetime import timedelta

class Config(object):
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    DEBUG = True
    CELERYBEAT_SCHEDULE = {
    'import_data': {
                       'task': 'pay_requests',
                       'schedule': timedelta(seconds=10)
                   },
    }

    JOBS = [
        {
            'id': 'updateLatestLedgersToRedis_job',  # 最新区块数据
            'func': 'app.utils.stellar_tasks:updateLatestLedgersToRedis',
            'args': (),
            'trigger': 'interval',
            'seconds': 1
        },
        # # {
        # #     'id': 'updateLatestTransationsToRedis_job',  # 最新事物数据
        # #     'func': 'app.utils.stellar_tasks:updateLatestTransationsToRedis',
        # #     'args': (),
        # #     'trigger': 'interval',
        # #     'seconds': 1
        # # },
        # # {
        # #     'id': 'updateLatestOpreationsToRedis_job',  # 最新操作数据
        # #     'func': 'app.utils.stellar_tasks:updateLatestOpreationsToRedis',
        # #     'args': (),
        # #     'trigger': 'interval',
        # #     'seconds': 1
        # # },
        {
            'id': 'updateLatestMainChainToRedis_job',
            'func': 'app.utils.stellar_tasks:updateLatestMainChainToRedis',
            'args': (),
            'trigger': 'interval',
            'seconds': 1
        }
    ]


class Development(Config):
    CONFIG_REDIS_PWD = os.environ.get("CONFIG_REDIS_PWD", "G%E5qk1T")
    CONFIG_REDIS_IPPORT = os.environ.get("CONFIG_REDIS_IPPORT", "101.132.188.48:6479")
    CONFIG_CONSUL_IP = "101.132.188.48"
    CONFIG_CONSUL_TOKEN = os.environ.get("CONFIG_CONSUL_TOKEN", "")
    CONFIG_ZIPKIN_SAMPLERATE = 100


class Production(Config):
    DEBUG = False
    CONFIG_REDIS_PWD = os.environ.get("CONFIG_REDIS_PWD", "")
    CONFIG_REDIS_IPPORT = os.environ.get("CONFIG_REDIS_IPPORT", "")
    CONFIG_CONSUL_IP = "xconsul"
    CONFIG_CONSUL_TOKEN = os.environ.get("CONFIG_CONSUL_TOKEN", "")
    CONFIG_ZIPKIN_SAMPLERATE = 1
