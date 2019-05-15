# encoding=utf8
import logging
import os
import fcntl
import atexit
from flask_redis import FlaskRedis
redisService = FlaskRedis()
from flask import Flask
from flask_environments import Environments
from flask_restplus import Api
from stellar_base import network
from flask_apscheduler import APScheduler
from app.basic.xianda_basic_api import basic_ns


SERVICE_NAME = "pay_dex"
APP_URL_PREFIX = "/v1/api/paydexchain"

NETWORK_ID = os.environ.get("CONFIG_NETWORK_ID", "XIANDA_DEV_NET")
NETWORK_PASSPHRASE = os.environ.get("CONFIG_NETWORK_PASSPHRASE", "xfin_core_network_v1.0.0 ; September 2018")
network.NETWORKS[NETWORK_ID] = NETWORK_PASSPHRASE



def create_app_api():
    app = Flask(SERVICE_NAME)

    config_env = Environments(app, default_env="DEVELOPMENT")
    config_env.from_object('config')


    config_redis_ipport = app.config["CONFIG_REDIS_IPPORT"]
    config_redis_password = app.config["CONFIG_REDIS_PWD"]
    app.config['REDIS_URL'] = "redis://:" + config_redis_password + "@" + config_redis_ipport + "/7"
    redisService.init_app(app)
    api_plus = Api(app, version="v1.0.0", title=SERVICE_NAME, prefix=APP_URL_PREFIX)

    # 首先打开（或创建）一个scheduler.lock文件，并加上非阻塞互斥锁。成功后创建scheduler并启动。
    f = open("scheduler.lock", "wb")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
    except:
        # 如果加文件锁失败，说明scheduler已经创建，就略过创建scheduler的部分。
        pass

    # 最后注册一个退出事件，如果这个flask项目退出，则解锁并关闭scheduler.lock文件的锁。
    def unlock():
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()

    atexit.register(unlock)

    BASIC_URL_PREFIX = "/basic"  # stellar基础接口(用户、区块浏览器等相关)
    api_plus.add_namespace(basic_ns, BASIC_URL_PREFIX)

    return app, api_plus
