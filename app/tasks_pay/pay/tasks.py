# coding: utf-8

# from app.tasks_pay.main import app
import logging

from app.constant import COINS_ISSUER, PHP_URL, PAYDEX_CODE, COIN_SEED, COIN_ISSUER
import requests

from stellar_base.operation import Payment  # operation:操作
from stellar_base.asset import Asset
from stellar_base.keypair import Keypair

from app.databases.database import OrderDetail, db, ExchangeDetail
from app.tasks_insert.insert_database.tasks import insert_tasks
from app.tasks_pay.main import app
from app.utils.code_msg import create_response, XDCodeMsg
from app.utils.stellar import create_envelope_submit, create_envelope_submits
from app.tasks_time.time_task import tasks as times
from app.tasks_stellar.stellar_task import tasks as stellar
# from app.tasks_insert import tasks as insert

from app.vres.sign_name import fun_var_kargs, random_str


@app.task(name='pay_requests')
def pay_requests(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
                 memo_oreder_id, merchant_private, fee, ):
    if memo_oreder_id == "兑换":
        pay_for_exchange(amount, coin_name, flow_status_id, pay_account_seed, sequence, fee,memo_oreder_id, )
    elif fee != "0" and memo_oreder_id != "兑换":
        pay_have_fee(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
                     memo_oreder_id, merchant_private, fee, )
    elif fee == "0" and memo_oreder_id != "兑换":
        pay_no_fee(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
                   memo_oreder_id)


# 含手续费的转账
def pay_have_fee(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence, memo_oreder_id,
                 merchant_private, fee, ):
    fee = str(fee)
    amount = str(amount)
    opts = list()
    opt_frist = Payment(dict(
        destination=collect_account_public,
        asset=Asset.native(),
        amount=str(fee) 
    ))
    opt_sceond = Payment(dict(
        destination=collect_account_public,
        asset=Asset.native() if coin_name == PAYDEX_CODE else Asset(coin_name, COINS_ISSUER),
        amount=str(amount)
    ))
    opts.append(opt_frist)
    opts.append(opt_sceond)
    user = Keypair.from_seed(merchant_private)
    users = user.address()
    is_success, stellar_hash = create_envelope_submit(user, sequence, memo_oreder_id, opts)
    if not is_success:
        try:
            order = OrderDetail()
            order.query.filter_by(orders=flow_status_id).update({'pay_status': 2})
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s转账成功存入数据哭失败' % (users, coin_name, amount))
            return False, u'paydex 修改状态失败转账失败'
        # 异步　请求恒星底层
        # stellar.pay_stellar(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,memo_oreder_id)
        stellar.pay_stellar.delay(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,memo_oreder_id)
        # 生产随机字符串
        rand_string = random_str()
        if rand_string is None:
            return False, u'随机字符串生成失败'

        # 验证签名
        sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                                  status='2',
                                  rand_string=rand_string
                                  )
        url = PHP_URL
        params = dict(flow_status_id=flow_status_id,
                      status='2',
                      sign=sign_name,
                      rand_string=rand_string
                      )
        print '111', params

        response = requests.post(url, data=params).json()
        if response.get('code') == 200:
            print "通知php成功"
        if response.get('code') != 200:
            return times.time_task.delay(params, stellar_hash, users, coin_name, amount, response, flow_status_id)
    else:
        # 生产随机字符串
        rand_string = random_str()
        if rand_string is None:
            return False, u'随机字符串生成失败'

        # 验证签名
        sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                                  success_no=stellar_hash,
                                  status='1',
                                  rand_string=rand_string
                                  )
        url = PHP_URL
        params = dict(flow_status_id=flow_status_id,
                      success_no=stellar_hash,
                      status='1',
                      sign=sign_name,
                      rand_string=rand_string
                      )
        print '111', params
        response = requests.post(url, data=params).json()
        print '2222', response
        if response.get('code') == 200:
            print "通知php成功***************************************************"
            if is_success:
                insert_tasks.delay(stellar_hash, flow_status_id, users, coin_name, amount)
                # insert_tasks(stellar_hash, flow_status_id, users, coin_name, amount)
                print "转账插入数据库成功!**********************************************"
            return True

        if response.get('code') != 200:
            return times.time_task.delay(params, stellar_hash, users, coin_name, amount, response, flow_status_id)

# 不含手续费的转账
def pay_no_fee(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
               memo_oreder_id):
    amount = str(amount)
    opts = list()
    opt = Payment(dict(
        destination=collect_account_public,
        asset=Asset.native() if coin_name == PAYDEX_CODE else Asset(coin_name, COINS_ISSUER),
        amount=str(amount)
    ))
    opts.append(opt)
    user = Keypair.from_seed(pay_account_seed)
    users = user.address()
    is_success, stellar_hash = create_envelope_submit(user, sequence, memo_oreder_id, opts)
    if not is_success:
        try:
            order = OrderDetail()
            order.query.filter_by(orders=flow_status_id).update({'pay_status': 2})
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s转账成功存入数据哭失败' % (users, coin_name, amount))
            return False, u'paydex 修改状态失败转账失败'
        # 异步　请求恒星底层
        # stellar.pay_stellar(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,memo_oreder_id)
        stellar.pay_stellar.delay(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,memo_oreder_id)

        # 生产随机字符串
        rand_string = random_str()
        if rand_string is None:
            return False, u'随机字符串生成失败'

        # 验证签名
        sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                                  status='2',
                                  rand_string=rand_string
                                  )
        url = PHP_URL
        params = dict(flow_status_id=flow_status_id,
                      status='2',
                      sign=sign_name,
                      rand_string=rand_string
                      )
        print '111', params
        response = requests.post(url, data=params).json()
        print '2222', response
        if response.get('code') == 200:
            print "通知php成功****************************************************"
        if response.get('code') != 200:
            return times.time_task.delay(params, stellar_hash, users, coin_name, amount, response, flow_status_id)
    else:
        # 生产随机字符串
        rand_string = random_str()
        if rand_string is None:
            return False, u'随机字符串生成失败'

        # 验证签名
        sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                                  success_no=stellar_hash,
                                  status='1',
                                  rand_string=rand_string
                                  )
        url = PHP_URL
        params = dict(flow_status_id=flow_status_id,
                      success_no=stellar_hash,
                      status='1',
                      sign=sign_name,
                      rand_string=rand_string
                      )
        print '111', params
        response = requests.post(url, data=params).json()
        print '2222', response
        if response.get('code') == 200:
            print "请求PHP成功******************************************"
            if is_success:
                insert_tasks.delay(stellar_hash, flow_status_id, users, coin_name, amount)
                # insert_tasks(stellar_hash, flow_status_id, users, coin_name, amount)
                print "转账插入数据库成功!"
            return True

        if response.get('code') != 200:
            return times.time_task.delay(params, stellar_hash, users, coin_name, amount, response, flow_status_id)


# 兑币
def pay_for_exchange(amount, coin_name, flow_status_id, exchange_account_seed, sequence, fee, memo_oreder_id):
    exchange_amount = amount.split("/")[0]
    get_amount = amount.split("/")[1]
    exchange_coin_name = coin_name.split("/")[0]
    get_coin_name = coin_name.split("/")[1]
    user = Keypair.from_seed(exchange_account_seed)
    finania_kp = Keypair.from_seed(COIN_SEED)
    user_keypair = [user, finania_kp]
    memo = u'{}转账'.format(coin_name)
    opts = list()
    if fee != "0":
        op = Payment({
            'destination': COIN_ISSUER,
            'asset': Asset.native() if exchange_coin_name == PAYDEX_CODE else Asset(exchange_coin_name, COINS_ISSUER),
            'amount': str(exchange_amount),
            'source': user.address()
        })
        op1 = Payment({
            'destination': COIN_ISSUER,
            'asset': Asset.native(),
            'amount': str(fee),
            'source': user.address()
        })
        op2 = Payment({
            'destination': user.address(),
            'asset': Asset.native() if get_coin_name == PAYDEX_CODE else Asset(get_coin_name, COINS_ISSUER),
            'amount': str(get_amount),
            'source': COIN_ISSUER
        })
        opts.append(op)
        opts.append(op1)
        opts.append(op2)
    else:
        op = Payment({
            'destination': COIN_ISSUER,
            'asset': Asset.native() if exchange_coin_name == PAYDEX_CODE else Asset(exchange_coin_name, COINS_ISSUER),
            'amount': str(exchange_amount),
            'source': user.address()
        })
        op2 = Payment({
            'destination': user.address(),
            'asset': Asset.native() if get_coin_name == PAYDEX_CODE else Asset(get_coin_name, COINS_ISSUER),
            'amount': str(get_amount),
            'source': COIN_ISSUER
        })
        opts.append(op)
        opts.append(op2)
    is_success, stellar_hash = create_envelope_submits(user_keypair, sequence, memo, opts)
    if not is_success:
        try:
            exchange = ExchangeDetail()
            exchange.query.filter_by(orders=flow_status_id).update({'pay_status': 2,'stellar_hash':stellar_hash})
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s转账成功存入数据哭失败' % (user_keypair, coin_name, amount))
            return False, u'paydex 修改状态失败转账失败'
        # 异步　请求恒星底层
        # stellar.pay_stellar(memo_oreder_id, amount, coin_name, flow_status_id, exchange_account_seed,
        #                     flow_status_id)
        stellar.pay_stellar.delay(memo_oreder_id, amount, coin_name, flow_status_id, exchange_account_seed,
                            flow_status_id)
        # 生产随机字符串
        rand_string = random_str()
        if rand_string is None:
            return False, u'随机字符串生成失败'

        # 验证签名
        sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                                  status='2',
                                  rand_string=rand_string
                                  )
        url = PHP_URL
        params = dict(flow_status_id=flow_status_id,
                      status='2',
                      sign=sign_name,
                      rand_string=rand_string
                      )
        print '111', params
        response = requests.post(url, data=params).json()
        print '2222', response
        if response.get('code') == 200:
            print "通知PHP成功****************************************"
        else:
            return times.time_task.delay(params, stellar_hash, is_success, user, coin_name, amount, response,
                                         flow_status_id)

    else:
        # 生产随机字符串
        rand_string = random_str()
        if rand_string is None:
            return False, u'随机字符串生成失败'

        # 验证签名
        sign_name = fun_var_kargs(flow_status_id=flow_status_id,
                                  success_no=stellar_hash,
                                  status='1',
                                  rand_string=rand_string
                                  )
        url = PHP_URL
        params = dict(flow_status_id=flow_status_id,
                      success_no=stellar_hash,
                      status='1',
                      sign=sign_name,
                      rand_string=rand_string
                      )
        print '111', params
        response = requests.post(url, data=params).json()
        print '2222', response
        if response.get('code') == 200:
            print "请求PHP成功******************************************"
            if is_success:
                # insert_tasks(stellar_hash, flow_status_id, user, coin_name, amount)
                insert_tasks.delay(stellar_hash, flow_status_id, user, coin_name, amount)
                return "插入数据库成功**************************************"

        if response.get('code') != 200:
            return times.time_task.delay(params, stellar_hash, is_success, user, coin_name, amount, response,
                                         flow_status_id)

