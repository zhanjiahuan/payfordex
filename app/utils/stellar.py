# coding:utf-8

import os
import requests
import hashlib
import json

from decimal import Decimal

from stellar_base.memo import TextMemo
from stellar_base.transaction import Transaction
from stellar_base.keypair import Keypair
from stellar_base.utils import account_xdr_object, StellarMnemonic
from stellar_base.transaction_envelope import TransactionEnvelope as Te
from stellar_base.asset import Asset

from app.utils.code_msg import XDCodeMsg
from app.utils.commons import str_num_to_decimal
from app.constant import STELLAR_SERVICE, PAYDEX_CODE, COINS_ISSUER, FEE


def stellar_service():
    """获取stellar服务url前缀"""

    # 返回值的格式 'http://101.132.188.48:8000'
    return STELLAR_SERVICE


def submit(xdr, envelope):
    """stellar事务提交xdr"""
    unsubmit_hash = hashlib.sha256(envelope.signature_base()).hexdigest()  # 计算事务的hash

    # 提交的url
    submit_url_prefix = stellar_service()
    submit_url = submit_url_prefix + '/transactions'

    # 提交的参数
    params = dict(tx=xdr)

    # 发送到网络,接收返回值
    submit_ret = requests.post(submit_url, data=params).json()
    return_hash = submit_ret.get('hash')  # 提交返回的hash值

    if return_hash is not None:
        return True, return_hash  # is_success,ret = submit()

    query_submit_url = submit_url_prefix + '/transactions/{}'.format(unsubmit_hash)
    query_ret = requests.get(query_submit_url).json()
    if query_ret.get('status') is None:
        return True, unsubmit_hash

    return False, submit_ret


def create_envelope_submit(user_kaykair, sequence, memo, opers, FEE=FEE):
    """事务封包,并提交"""
    tx = Transaction(source=user_kaykair.address().decode(),  # 事务发起着的公钥
                     opts={'sequence': sequence,  # 事务发起着的序列号
                           'memo': TextMemo(memo),  # 备注
                           'fee': len(opers) * FEE,  # 手续费
                           'operations': opers, }, )  # 操作
    envelope = Te(tx=tx, opts=dict(network_id='XIANDA_DEV_NET'))  # 操作封包的类Te
    envelope.sign(user_kaykair)  # 事务发起着签名
    te = envelope.xdr()  # 转换xdr格式数据
    # te_hash = hashlib.sha256(envelope.signature_base()).hexdigest()
    # return te_hash,te,envelope
    return submit(te, envelope)


def create_envelope_submits(user_kaykair, sequence, memo, opers, FEE=FEE):
    """事务封包,并提交"""
    tx = Transaction(source=user_kaykair[0].address().decode(),  # 事务发起着的公钥
                     opts={'sequence': sequence,  # 事务发起着的序列号
                           'memo': TextMemo(memo),  # 备注
                           'fee': len(opers) * FEE,  # 手续费
                           'operations': opers, }, )  # 操作
    envelope = Te(tx=tx, opts=dict(network_id='XIANDA_DEV_NET'))  # 操作封包的类Te
    for i in user_kaykair:
        print 2222, user_kaykair

        envelope.sign(i)
    # envelope.sign(user_kaykair)  # 事务发起着签名
    te = envelope.xdr()  # 转换xdr格式数据
    return submit(te, envelope)

def create_envelope(user_kaykair, sequence, memo, opers, FEE=0):
    """事务封包"""
    tx = Transaction(source=user_kaykair.address().decode(),  # 事务发起着的公钥
                     opts={'sequence': sequence,  # 事务发起着的序列号
                           'memo': TextMemo(memo),  # 备注
                           'fee': len(opers) * FEE,  # 手续费
                           'operations': opers, }, )  # 操作
    envelope = Te(tx=tx, opts=dict(network_id='XIANDA_DEV_NET'))  # 操作封包的类Te
    envelope.sign(user_kaykair)  # 事务发起着签名
    # te = envelope.xdr()  # 转换xdr格式数据
    te_hash = hashlib.sha256(envelope.signature_base()).hexdigest()
    return te_hash
    # return submit(te, envelope)


def check_stellar_account(stellar_account):
    """检查stellar公钥是否合法,合法返回True 不合法返回False"""
    try:
        # stellar 内部提供的方法 知道有什么用就行了
        account_xdr_object(stellar_account)
    except:
        return False
    return True


def mnemonic_keypair(mnemonicLang='english'):
    """生成stellar账户,字典返回"""
    sm = StellarMnemonic(mnemonicLang)
    mnemonic = sm.generate()
    keypair = Keypair.deterministic(mnemonic, lang=mnemonicLang)
    return dict(mnemonic=str(mnemonic),  # 助记词
                account=keypair.address(),  # stellar公钥
                seed=keypair.seed())  # stellar秘钥


def stellar_account_info(stellar_account):
    """获取stellar账户信息 序列号 余额"""
    url_prefix = stellar_service()
    url = url_prefix + '/accounts/{}'.format(stellar_account)
    ret = requests.get(url).json()
    balances = ret.get('balances')
    sequence = ret.get('sequence')
    return sequence, balances


# def stellar_sequence(stellar_account):
#     """stellar序列号"""
#     ret = stellar_account_info(stellar_account)
#     sequence = ret.get('sequence')
#     return sequence


# def stellar_balance(stellar_account):
#     """stellar账户余额 列表"""
#     ret = stellar_account_info(stellar_account)
#     balances = ret.get('balances')
#     return balances


def asset_obj(asset_name):
    '''组建资产对象'''
    return Asset(asset_name, COINS_ISSUER)


def pay_object(pay_secret_key):
    '''通过秘钥来获取公钥'''
    par_object = Keypair.from_seed(pay_secret_key)  # 实例化秘钥对象
    # address() 通过秘钥对象获取它的公钥 记获取出来的是bytes类型需要转码
    assert_issuer = par_object.address().decode()
    return assert_issuer


if __name__ == '__main__':
    if not check_stellar_account('GD6GCFSDQJCSJQS3I3L7WAZ37QI7N5RL5IMDVF7DFOR7UBNO74ZJFTYX'):
        print('账户不合法')
