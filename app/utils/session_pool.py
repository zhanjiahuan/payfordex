# coding:utf-8

import requests
from requests.adapters import HTTPAdapter

POOL_CONNECTIONS = 100
POOL_MAXSIZE = 1000

class SessionPool(object):
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SessionPool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.sessionPool = self.session_pool()

    def session_pool(self):
        sessionPool = requests.Session()
        sessionPool.mount('http://', HTTPAdapter(pool_connections=POOL_CONNECTIONS, pool_maxsize=POOL_MAXSIZE))
        sessionPool.mount('https://', HTTPAdapter(pool_connections=POOL_CONNECTIONS, pool_maxsize=POOL_MAXSIZE))
        return sessionPool

if __name__ == '__main__':
    a = SessionPool()
    b = SessionPool()
    print a is b
    print a.sessionPool is b.sessionPool