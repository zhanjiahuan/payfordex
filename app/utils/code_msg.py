# encoding=utf8

import json
import collections


class XDCodeMsg:
    CodeMsg = collections.namedtuple('CodeMsg', ['code', 'msg'])
    SUCCESS = CodeMsg(200, U'成功')
    ACCOUNT_NOT_ACTIVE = CodeMsg(1002, U'未激活账户')

def create_response(ret_cm, data=None):
    if ret_cm.code == XDCodeMsg.SUCCESS.code:
        ret = XDCommonJsonRet(code=ret_cm.code,
                              success=True,
                              msg=ret_cm.msg,
                              data=data)
    else:
        ret = XDCommonJsonRet(code=ret_cm.code,
                              success=False,
                              msg=ret_cm.msg,
                              data=data)
    return ret.toJson()


class XDCommonJsonRet():
    """服务统一返回接口格式"""

    def __init__(self, code, success, msg, data):
        self.code = code
        self.msg = msg
        self.data = data
        self.success = success

    def toJsonStr(self):
        return json.dumps(self.__dict__)

    def toJson(self):
        return self.__dict__


if __name__ == '__main__':
    print (XDCodeMsg.SUCCESS.__dict__.get('code'))
