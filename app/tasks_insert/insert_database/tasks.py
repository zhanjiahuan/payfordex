# coding: utf-8

import logging
# from app.tasks_pay.main import app

from app.databases.database import OrderDetail, db,ExchangeDetail
from app.tasks_insert.main import app


@app.task(name='insert_tasks')
def insert_tasks(stellar_hash, flow_status_id, users, coin_name, amount):
    if len(coin_name)>6:
        try:
            exchange = ExchangeDetail()
            exchange.query.filter_by(orders=flow_status_id).update(
                {'stellar_hash': str(stellar_hash), 'pay_status': 3, 'status': 1, "ask_frequency": 1})
            # order.hash = hash
            # order.pay_status = 3
            # order.status = 1
            # order = OrderDetail(hash=hash,status=1, pay_status=3)
            # db.session.add_all([order])
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s转账成功存入数据哭失败' % (users, coin_name, amount))
            return False, u'paydex 修改状态失败转账失败'
        return True, u'转账成功'
    else:
        try:
            order = OrderDetail()
            order.query.filter_by(orders=flow_status_id).update(
                {'hash': str(stellar_hash), 'pay_status': 3, 'status': 1,"ask_frequency":1})
            # order.hash = hash
            # order.pay_status = 3
            # order.status = 1
            # order = OrderDetail(hash=hash,status=1, pay_status=3)
            # db.session.add_all([order])
            db.session.commit()
        except Exception as e:
            logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s转账成功存入数据哭失败' % (users, coin_name, amount))
            return False, u'paydex 修改状态失败转账失败'
        return True, u'转账成功'