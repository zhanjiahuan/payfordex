# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')
import hashlib
import hmac
import base64
import json
import time
import random
import string
import requests
from app.constant import APP_SIGN, AES_KEY, AES_IV
from Crypto.Cipher import AES
from app.utils.code_msg import XDCodeMsg
from app.constant import PHP_URL


def fun_var_kargs(**kwargs):
    for i in kwargs.keys():
        if kwargs[i] is None or kwargs[i] == "":
            del (kwargs[i])
    strs = ''
    for key in sorted(kwargs):
        if len(strs) == 0:
            strs += key + '=' + kwargs[key]
        else:
            strs += '&' + key + '=' + kwargs[key]
    print strs


    # print strs
    message = bytes(strs).encode('utf-8')
    secret = bytes(APP_SIGN).encode('utf-8')

    # APP_SIGN='Y5Ik9hp4koWx7Ep8YbjOEFavgehuhGEd'
    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    sign_name = signature.upper()
    return sign_name


    # QNR8UCQJGGD55POHUSABNVIGOOJ67HC6BTRY4QXLVZC =
    # sha256 = hashlib.sha256()
    # sha256.update(strs.encode('utf-8'))
    # res = sha256.hexdigest()
    # print res.upper()


# pay_account_seed="SBCHAGLMZTOH2RO4AZQ55VK5QJUYVEGHHJEHZPL7O6E3P2LZCDDME77C"
# memo_oreder_id='123'
# coin_name='BTC'
# amount='10'
# # flow_status_id="32343"
# # rand_string="guhgjhiofvsd"
# # collect_account_public="GC2CZS57U5ICHLXPDI6KGAD75F4FHWQPFOEEYPF5OCMAS46N2ZYEXE6J"
# #
# a = fun_var_kargs(pay_account_seed=pay_account_seed,
#                   memo_oreder_id=memo_oreder_id,
#                   coin_name=coin_name,
#                   amount=amount,)
#                   # flow_status_id=flow_status_id,
#                   # rand_string=rand_string,
#                   # collect_account_public=collect_account_public)
# print a



def decryptUserSeed(encrypt_user_seed):
    """AES解密, 返回字符串"""
    key = AES_KEY  # 16,24,32位长的密码
    iv = AES_IV
    unpad = lambda s: s[0:-ord(s[-1])]
    decrypted_bytes = bytes(encrypt_user_seed).encode(encoding='utf-8')
    try:
        data = base64.b64decode(decrypted_bytes)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # AES解密
        data = unpad(cipher.decrypt(data)).decode('utf-8')
    except Exception:
        data = None
    return data


def decryptStellarSeed(encrypt_seed):
    # 解密user_seed,校验时效
    seed_info = decryptUserSeed(encrypt_seed)
    if not seed_info:
        return XDCodeMsg.CodeMsg(1002, U'无效密钥')

    seed_info = json.loads(seed_info)
    send_time = seed_info.get('time')
    if time.time() - send_time > 20:
        return XDCodeMsg.CodeMsg(1002, U'密钥过时')

    user_seed = seed_info.get('seed')
    return user_seed


# 用户秘钥加密
def seedEncrypt(data):
    key = AES_KEY  # 16,24,32位长的密码
    iv = AES_IV
    bs = AES.block_size
    pad = lambda s: s + (bs - len(s) % bs) * chr(bs - len(s) % bs)
    iv = bytes(iv).encode('utf-8')
    password = bytes(key).encode('utf-8')  # 16,24,32位长的密码
    cipher = AES.new(password, AES.MODE_CBC, iv)
    data = cipher.encrypt((pad(data)).encode(encoding='utf-8'))

    data = base64.b64encode(data)
    data = data.decode("utf-8")
    return data


# 随机字符串
def random_str():
    # time.sleep(2)
    strings = ''.join(random.sample(string.ascii_letters + string.digits, 20))
    return strings

def requests_php_api(flow_status_id,stellar_hash):
    # 生产随机字符串
    rand_string = random_str()

    # 验证签名
    sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                              success_no=stellar_hash,
                              status='1',
                              rand_string=rand_string
                              )
    # print '3333333333333333', sign_name
    # php 接口地址
    url = PHP_URL
    params = dict(flow_status_id=flow_status_id,
                  success_no=stellar_hash,
                  status='1',
                  sign=sign_name,
                  rand_string=rand_string
                  )
    response = requests.post(url, data=params).json()
    return response

