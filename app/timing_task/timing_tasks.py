# coding: utf-8
import requests
import logging
import time
import string
import random

from app.vres.sign_name import fun_var_kargs,random_str
from app.databases.database import OrderDetail, SteallarTrueOverTimeInfo, SteallarFalseOverTimeInfo, db
from app.constant import PHP_URL, STELLAR_SERVICE, PYTHON_PAY_URL

# 请求底层真超时处理
def requests_stellar_true_over_time():
    '''
    true_over_time_orderb表, 字段名
    －－－－－－－－－－－－－－－－－－－－
    true_over_time_orders   # 订单号
    true_over_time__status    # 1=转账成功 ， 2=转账失败 处理成功了该状态为一
    true_over_time_public   # 收款账户公钥
    true_over_time_pay_account_seed   # 付款账号秘钥
    true_over_time_amount   # 金额,浮点数字符串
    true_over_time_coin_name   # 付款货币名称
    true_over_time_memo_oreder_id   # 转账备注
    '''
    true_order = SteallarTrueOverTimeInfo()
    ret = SteallarTrueOverTimeInfo.query.filter_by(false_over_time_status=2).first()
    true_over_time_orders = ret.true_over_time_orders
    true_over_time_public = ret.true_over_time_public
    true_over_time_pay_account_seed = ret.true_over_time_pay_account_seed
    true_over_time_amount = ret.true_over_time_amount
    true_over_time_coin_name = ret.true_over_time_coin_name
    true_over_time_memo_oreder_id = ret.true_over_time_memo_oreder_id

    '''
    请求python转账接口时,需要传递的参数名
            'collect_account_public': u'收款账户公钥',
            'amount': u'金额,浮点数字符串',
            'coin_name': u'付款货币名称',
            'memo_oreder_id': u"转账备注",
            'pay_account_seed': u'付款账户密钥',
            'flow_status_id': u'转账订单号'

    '''
    # 随机字符串
    rand_string = ''.join(random.sample(string.ascii_letters + string.digits, 20))
    # 验证签名
    sign_name = fun_var_kargs(collect_account_public=true_over_time_public,
                              amount=true_over_time_amount,
                              coin_name=true_over_time_coin_name,
                              memo_oreder_id=true_over_time_memo_oreder_id,
                              pay_account_seed=true_over_time_pay_account_seed,
                              flow_status_id=true_over_time_orders,
                              rand_string=rand_string,
                              )

    opst = dict(collect_account_public=true_over_time_public,
                amount=true_over_time_amount,
                coin_name=true_over_time_coin_name,
                memo_oreder_id=true_over_time_memo_oreder_id,
                pay_account_seed=true_over_time_pay_account_seed,
                flow_status_id=true_over_time_orders,
                rand_string=rand_string,
                sign=sign_name,
                )
    # 请求python 转账接口
    url = PYTHON_PAY_URL
    response = requests.post(url, opst).json()
    if response.get('code') == 200:
        time.sleep(5)
        ret = OrderDetail.query.filter_by(orders=true_over_time_orders).first()
        status = ret.amount
        pay_status = ret.pay_status
        if status == 1 and pay_status == 3:
            try:
                true_order.query.filter_by(true_over_time_orders=true_over_time_orders).update(
                    {'true_over_time__status': 1, })
                db.session.commit()
            except Exception as e:
                logging.error(
                    str(e) + 'true_over_time__status:{}, true_over_time_orders:{}'.format(true_over_time_orders, 1))
                return False, 'true_over_time_order表　requests_steallar_false_over_time()定时任务中　 修改状态失败转账失败'


# 请求底层假超时处理
def requests_steallar_false_over_time():
    '''
    false_over_time_order表字段名：
    －－－－－－－－－－－－－－－－－－
    false_over_time_orders   # 订单号
    false_over_time_count_hash   # 计算哈希
    false_over_time_status   # 1=转账成功 ， 2=转账失败 php状态
    '''
    flase_order = SteallarFalseOverTimeInfo()
    ret = SteallarFalseOverTimeInfo.query.filter_by(false_over_time_status=2).first()
    false_over_time_orders = ret.false_over_time_orders
    false_over_time_count_hash = ret.false_over_time_count_hash

    # # 请求恒星底层
    # url = STELLAR_SERVICE + '/transactions/{}'.format(false_over_time_count_hash)
    # response = requests.get(url).json()
    # if response.get('hash') is not None:
    # 生产随机字符串
    rand_string = random_str()
    # 验证签名
    sign_name = fun_var_kargs(flow_status_id=false_over_time_orders,
                              success_no=false_over_time_count_hash,
                              status='1',
                              rand_string=rand_string
                              )
    # php 接口地址
    url = PHP_URL
    params = dict(flow_status_id=false_over_time_orders,
                  success_no=false_over_time_count_hash,
                  status='1',
                  sign=sign_name,
                  rand_string=rand_string
                  )
    # 请求php接口
    # url = PHP_URL
    # params = dict(flow_status_id=false_over_time_orders,
    #               success_no=false_over_time_count_hash,
    #               status=1)
    response = requests.post(url=url, data=params).json()
    if response.get('code') == 200:
        # 请求php接口成功
        order = OrderDetail()
        ret = OrderDetail.query.filter_by(orders=false_over_time_orders, pay_status=1).first()
        pay_account_seed = ret.pay_account_seed
        coin_name = ret.coin_name
        amount = ret.amount

        # 修改order表中数据
        try:
            order.query.filter_by(orders=false_over_time_orders).update(
                {'hash': str(false_over_time_count_hash), 'pay_status': 3, 'status': 1, })
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + 'user:%s, coin_name:%s, amount:%s 1' % (pay_account_seed, coin_name, amount))
            return False, 'order表　requests_steallar_false_over_time()定时任务中　 修改状态失败转账失败'

        # 修改false_over_time_order表中数据
        try:
            flase_order.query.filter_by(false_over_time_orders=false_over_time_orders).update(
                {'false_over_time_status': 1, })
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + 'false_over_time_count_hash:{}'.format(false_over_time_count_hash))
            return False, 'false_over_time_order表, requests_steallar_false_over_time()定时任务中 修改状态失败转账失败'
        return True, '转账成功'
