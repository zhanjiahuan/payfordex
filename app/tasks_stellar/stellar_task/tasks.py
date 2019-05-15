# coding: utf-8
# from app.tasks_pay.main import app

# from app.timing_task.get_setllar import setllar_bottom_pay
import requests
import logging

from app.databases.database import OrderDetail, SteallarFalseOverTimeInfo, SteallarTrueOverTimeInfo, db, ExchangeDetail
from app.constant import STELLAR_SERVICE
from app.tasks_stellar.main import app


@app.task(name='pay_stellar')
def pay_stellar(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,memo_oreder_id):
    if collect_account_public == "兑换":
        # 获取计算哈希
        stellar_hash = ExchangeDetail.query.filter_by(orders=flow_status_id).first().stellar_hash
        # 拼接stellar底层节点,查询交易是否成功
        url = STELLAR_SERVICE + '/transactions/{}'.format(stellar_hash)

        response = requests.get(url).json()
        if response.get('hash') is not None:
            try:
                # 假超时信息存入mysql
                false_order = SteallarFalseOverTimeInfo(false_over_time_orders=flow_status_id,
                                                        false_over_time_count_hash=stellar_hash,
                                                        false_over_time_status=2)
                db.session.add_all([false_order])
                db.session.commit()
            except Exception as e:
                logging.error(
                    str(e) + 'false_over_time_orders:%s, false_over_time_count_hash:%s 转账成功底层假超时存入数据哭失败' % (
                        flow_status_id, stellar_hash))
                return False, '底层假超时信息存储失败'

        else:
            try:
                # 真超时信息存入mysql
                # 转账备注进行字符串拼接，用于重新请求python转账接口时用于判断，因为为订单号不可重复第一次请求已经存进数据库了
                memo_oreder_id = memo_oreder_id + ':' + 'true'
                true_order = SteallarTrueOverTimeInfo(true_over_time_orders=flow_status_id,
                                                      true_over_time__status=2,
                                                      true_over_time_public=collect_account_public,
                                                      true_over_time_pay_account_seed=pay_account_seed,
                                                      true_over_time_amount=amount,
                                                      true_over_time_coin_name=coin_name,
                                                      true_over_time_memo_oreder_id=memo_oreder_id, )
                db.session.add_all([true_order])
                db.session.commit()
            except Exception as e:
                logging.error(
                    str(e) + 'true_over_time_orders:%s,'
                             'rue_over_time_public:%s, '
                             'true_over_time_pay_account_seed:%s '
                             'rue_over_time_amount:%s,'
                             'true_over_time_coin_name:%s,'
                             'true_over_time_memo_oreder_id:%s,'
                             '转账成功存入数据哭失败' % (
                        flow_status_id, collect_account_public, pay_account_seed, amount, coin_name, memo_oreder_id))
                return False, '底层真超时信息存储失败'
    else:
        # 获取计算哈希
        stellar_hash = OrderDetail.query.filter_by(orders=flow_status_id).first().count_hash
        # 拼接stellar底层节点,查询交易是否成功
        url = STELLAR_SERVICE + '/transactions/{}'.format(stellar_hash)

        response = requests.get(url).json()
        if response.get('hash') is not None:
            try:
                # 假超时信息存入mysql
                false_order = SteallarFalseOverTimeInfo(false_over_time_orders=flow_status_id,
                                                        false_over_time_count_hash=stellar_hash, false_over_time_status=2)
                db.session.add_all([false_order])
                db.session.commit()
            except Exception as e:
                logging.error(
                    str(e) + 'false_over_time_orders:%s, false_over_time_count_hash:%s 转账成功底层假超时存入数据哭失败' % (
                        flow_status_id, stellar_hash))
                return False, '底层假超时信息存储失败'

        else:
            try:
                # 真超时信息存入mysql

                # 转账备注进行字符串拼接，用于重新请求python转账接口时用于判断，因为为订单号不可重复第一次请求已经存进数据库了
                memo_oreder_id = memo_oreder_id + ':' + 'true'
                true_order = SteallarTrueOverTimeInfo(true_over_time_orders=flow_status_id,
                                                      true_over_time__status=2,
                                                      true_over_time_public=collect_account_public,
                                                      true_over_time_pay_account_seed=pay_account_seed,
                                                      true_over_time_amount=amount,
                                                      true_over_time_coin_name=coin_name,
                                                      true_over_time_memo_oreder_id=memo_oreder_id, )
                db.session.add_all([true_order])
                db.session.commit()
            except Exception as e:
                logging.error(
                    str(e) + 'true_over_time_orders:%s,'
                             'rue_over_time_public:%s, '
                             'true_over_time_pay_account_seed:%s '
                             'rue_over_time_amount:%s,'
                             'true_over_time_coin_name:%s,'
                             'true_over_time_memo_oreder_id:%s,'
                             '转账成功存入数据哭失败' % (
                        flow_status_id, collect_account_public, pay_account_seed, amount, coin_name, memo_oreder_id))
                return False, '底层真超时信息存储失败'
