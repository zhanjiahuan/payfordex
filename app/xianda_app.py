#! /usr/bin/env python
# -*- coding: utf-8 -*-

# 本页面为程序入口，尽量用于配制，精简代码
import logging
from app import create_app_api,APP_URL_PREFIX
from app.utils.code_msg import XDCommonJsonRet

from app.logs import init_log
from app.constant import *
from app.databases.database import db


app,api_plus = create_app_api()


init_log()
# 统一404处理
@app.errorhandler(404)
def page_not_not_found(error):
    return XDCommonJsonRet(code=404,
                           success=False,
                           msg="404 Not Found . there is not this api",
                           data="").toJsonStr()


# 统一异常处理
@api_plus.errorhandler
def default_error_handler(exception):
    # 异常栈写入
    logging.error(exception)
    return XDCommonJsonRet(code=500,
                           success=False,
                           msg=exception.message,
                           data="server exception capture").toJson()





if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=58482)

