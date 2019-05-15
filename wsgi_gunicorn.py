# encoding=utf8
import logging
from logging.handlers import WatchedFileHandler

from app.xianda_app import app
import gevent.monkey
import redis.connection

if __name__ == "__main__":
    gevent.monkey.patch_all()
    redis.connection.socket = gevent.socket
    acclog = logging.getLogger('gunicorn.access')
    acclog.addHandler(WatchedFileHandler('/logs/pyservice_log/pyservice_access.log'))
    acclog.propagate = False
    errlog = logging.getLogger('gunicorn.error')
    errlog.addHandler(WatchedFileHandler('/logs/pyservice_log/pyservice_error.log'))
    errlog.propagate = False

    print app.config
    app.run(DUBUG = True)
