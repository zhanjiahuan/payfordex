# coding: utf-8
import requests
import time
import logging
from app.constant import PHP_URL
from app.databases.database import OrderDetail, db,ExchangeDetail
from app.tasks_time.main import app


# 不返回200，会在25小时以内完成8次通知（通知的间隔频率一般是：4m,10m,10m,1h,2h,6h,15h）；才会结束通知发送。
@app.task(name='time_task')
def time_task(params, stellar_hash, users, coin_name, amount, flow_status_id):
    if len(coin_name)>6:
        url = PHP_URL
        exchange = ExchangeDetail()
        time.sleep(60 * 4)
        response = requests.post(url=url, data=params).json()
        if response.get('code') == 200:
            # 请求php接口成功
            try:
                exchange.query.filter_by(orders=flow_status_id).update(
                    {'hash': stellar_hash, 'pay_status': 3, 'status': 1, 'ask_frequency': 2})
                db.session.commit()
            except Exception as e:
                logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 2' % (users, coin_name, amount))
                return False, u'paydex 修改状态失败转账失败'
            return True, u'转账成功'
        else:
            time.sleep(60 * 10)
            response = requests.post(url=url, data=params).json()
            if response.get('code') == 200:
                # 请求php接口成功
                try:
                    exchange.query.filter_by(orders=flow_status_id).update(
                        {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 3})
                    db.session.commit()
                except Exception as e:
                    logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 3' % (users, coin_name, amount))
                    return False, u'paydex 修改状态失败转账失败'

                return True, u'转账成功'

            else:
                time.sleep(60 * 10)
                response = requests.post(url=url, data=params).json()
                if response.get('code') == 200:
                    # 请求php接口成功
                    try:
                        exchange.query.filter_by(orders=flow_status_id).update(
                            {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 4})
                        db.session.commit()
                    except Exception as e:
                        logging.error(
                            str(e) + u'user:%s, coin_name:%s, amount:%s 4' % (users, coin_name, amount))
                        return False, u'paydex 修改状态失败转账失败'

                    return True, u'转账成功'

                else:
                    time.sleep(60 * 60)
                    response = requests.post(url=url, data=params).json()
                    if response.get('code') == 200:
                        # 请求php接口成功
                        try:
                            exchange.query.filter_by(orders=flow_status_id).update(
                                {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 5})
                            db.session.commit()
                        except Exception as e:
                            logging.error(e)
                            logging.error(
                                str(e) + u'user:%s, coin_name:%s, amount:%s 5' % (users, coin_name, amount))
                            return False, u'paydex 修改状态失败转账失败'

                        return True, u'转账成功'

                    else:
                        time.sleep(60 * 120)
                        response = requests.post(url=url, data=params).json()
                        if response.get('code') == 200:
                            # 请求php接口成功
                            try:
                                exchange.query.filter_by(orders=flow_status_id).update(
                                    {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 6})
                                db.session.commit()
                            except Exception as e:
                                logging.error(
                                    str(e) + u'user:%s, coin_name:%s, amount:%s 6' % (users, coin_name, amount))
                                return False, u'paydex 修改状态失败转账失败'

                            return True, u'转账成功'

                        else:
                            time.sleep(60 * 360)
                            response = requests.post(url=url, data=params).json()
                            if response.get('code') == 200:
                                # 请求php接口成功
                                try:
                                    exchange.query.filter_by(orders=flow_status_id).update(
                                        {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 7})
                                    db.session.commit()
                                except Exception as e:
                                    logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 7' % (
                                        users, coin_name, amount))
                                    return False, u'paydex 修改状态失败转账失败'

                                return True, u'转账成功'

                            else:
                                time.sleep(60 * 900)
                                response = requests.post(url=url, data=params).json()
                                if response.get('code') == 200:
                                    # 请求php接口成功
                                    try:
                                        exchange.query.filter_by(orders=flow_status_id).update(
                                            {'hash': str(hash), 'pay_status': 3, 'status': 1,
                                             'ask_frequency': 8})
                                        db.session.commit()
                                    except Exception as e:
                                        logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 8' % (
                                            users, coin_name, amount))
                                        return False, u'paydex 修改状态失败转账失败'

                                    return True, u'转账成功'

                                else:
                                    try:
                                        exchange.query.filter_by(orders=flow_status_id).update(
                                            {'hash': str(hash), 'pay_status': 2, 'status': 2,
                                             'ask_frequency': 9})
                                        db.session.commit()
                                    except Exception as e:
                                        logging.error(
                                            str(e) + u'user:%s, coin_name:%s, amount:%s 9　请求ＰPHP接口超时转账失败' % (
                                                users, coin_name, amount))
                                        return False, u'paydex 修改状态失败转账失败'

                                    return u'转账失败'

    else:
        url = PHP_URL
        order = OrderDetail()
        time.sleep(60 * 4)
        response = requests.post(url=url, data=params).json()
        if response.get('code') == 200:
            # 请求php接口成功
            try:
                order.query.filter_by(orders=flow_status_id).update(
                    {'hash': stellar_hash, 'pay_status': 3, 'status': 1, 'ask_frequency': 2})
                db.session.commit()
            except Exception as e:
                logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 2' % (users, coin_name, amount))
                return False, u'paydex 修改状态失败转账失败'
            return True, u'转账成功'
        else:
            time.sleep(60 * 10)
            response = requests.post(url=url, data=params).json()
            if response.get('code') == 200:
                # 请求php接口成功
                try:
                    order.query.filter_by(orders=flow_status_id).update(
                        {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 3})
                    db.session.commit()
                except Exception as e:
                    logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 3' % (users, coin_name, amount))
                    return False, u'paydex 修改状态失败转账失败'

                return True, u'转账成功'

            else:
                time.sleep(60 * 10)
                response = requests.post(url=url, data=params).json()
                if response.get('code') == 200:
                    # 请求php接口成功
                    try:
                        order.query.filter_by(orders=flow_status_id).update(
                            {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 4})
                        db.session.commit()
                    except Exception as e:
                        logging.error(
                            str(e) + u'user:%s, coin_name:%s, amount:%s 4' % (users, coin_name, amount))
                        return False, u'paydex 修改状态失败转账失败'

                    return True, u'转账成功'

                else:
                    time.sleep(60 * 60)
                    response = requests.post(url=url, data=params).json()
                    if response.get('code') == 200:
                        # 请求php接口成功
                        try:
                            order.query.filter_by(orders=flow_status_id).update(
                                {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 5})
                            db.session.commit()
                        except Exception as e:
                            logging.error(e)
                            logging.error(
                                str(e) + u'user:%s, coin_name:%s, amount:%s 5' % (users, coin_name, amount))
                            return False, u'paydex 修改状态失败转账失败'

                        return True, u'转账成功'

                    else:
                        time.sleep(60 * 120)
                        response = requests.post(url=url, data=params).json()
                        if response.get('code') == 200:
                            # 请求php接口成功
                            try:
                                order.query.filter_by(orders=flow_status_id).update(
                                    {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 6})
                                db.session.commit()
                            except Exception as e:
                                logging.error(
                                    str(e) + u'user:%s, coin_name:%s, amount:%s 6' % (users, coin_name, amount))
                                return False, u'paydex 修改状态失败转账失败'

                            return True, u'转账成功'

                        else:
                            time.sleep(60 * 360)
                            response = requests.post(url=url, data=params).json()
                            if response.get('code') == 200:
                                # 请求php接口成功
                                try:
                                    order.query.filter_by(orders=flow_status_id).update(
                                        {'hash': str(hash), 'pay_status': 3, 'status': 1, 'ask_frequency': 7})
                                    db.session.commit()
                                except Exception as e:
                                    logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 7' % (
                                        users, coin_name, amount))
                                    return False, u'paydex 修改状态失败转账失败'

                                return True, u'转账成功'

                            else:
                                time.sleep(60 * 900)
                                response = requests.post(url=url, data=params).json()
                                if response.get('code') == 200:
                                    # 请求php接口成功
                                    try:
                                        order.query.filter_by(orders=flow_status_id).update(
                                            {'hash': str(hash), 'pay_status': 3, 'status': 1,
                                             'ask_frequency': 8})
                                        db.session.commit()
                                    except Exception as e:
                                        logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s 8' % (
                                            users, coin_name, amount))
                                        return False, u'paydex 修改状态失败转账失败'

                                    return True, u'转账成功'

                                else:
                                    try:
                                        order.query.filter_by(orders=flow_status_id).update(
                                            {'hash': str(hash), 'pay_status': 2, 'status': 2,
                                             'ask_frequency': 9})
                                        db.session.commit()
                                    except Exception as e:
                                        logging.error(
                                            str(e) + u'user:%s, coin_name:%s, amount:%s 9　请求ＰPHP接口超时转账失败' % (
                                                users, coin_name, amount))
                                        return False, u'paydex 修改状态失败转账失败'

                                    return u'转账失败'
