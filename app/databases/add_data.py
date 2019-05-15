# # coding: utf-8
#
# from flask import Flask
#
# from app.constant import COINS_ISSUER, PHP_URL, PAYDEX_CODE
# import logging
# import requests
# import random
# import string
#
# from app.databases.database import OrderDetail, db
# from stellar_base.operation import CreateAccount, ChangeTrust, Payment  # operation:操作
# from stellar_base.asset import Asset
# from stellar_base.keypair import Keypair
#
# from app.utils.stellar import create_envelope_submit
# from app.tasks_pay.time_task import tasks_pay as ta
# from app.tasks_pay.stellar_task import tasks_pay
# from app.vres.sign_name import fun_var_kargs, random_str
#
#
# def get_pay_info_mysql(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
#                        memo_oreder_id):
#     from app.tasks_pay import pay_tasks
#     # 组建事务字典
#     print u'接收到任务'
#     amount = str(amount)
#     opts = list()
#     opt = Payment(dict(
#         destination=collect_account_public,
#         asset=Asset.native() if coin_name == PAYDEX_CODE else Asset(coin_name, COINS_ISSUER),
#         amount=str(amount)
#     ))
#     opts.append(opt)
#     user = Keypair.from_seed(pay_account_seed)
#     users = user.address()
#     is_success, stellar_hash = create_envelope_submit(user, sequence, memo_oreder_id, opts)
#     if stellar_hash is None:
#         # 异步　请求恒星底层
#         tasks_pay.pay_stellar.apply_async((collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,
#                                            memo_oreder_id), retry=True, retry_policy={
#                                                                                         'max_retries': 3,
#                                                                                         'interval_start': 0,
#                                                                                         'interval_step': 0.2,
#                                                                                         'interval_max': 0.2,
#                                                                                     })
#         return False, u'恒星底层请求超时'
#     # 生产随机字符串
#     rand_string = random_str()
#     if rand_string is None:
#         return False, u'随机字符串生成失败'
#
#     # 验证签名
#     sign_name = fun_var_kargs(flow_status_id=flow_status_id,
#                               success_no=stellar_hash,
#                               status='1',
#                               rand_string=rand_string
#                               )
#     # print '3333333333333333', sign_name
#     # php 接口地址
#     url = PHP_URL
#     params = dict(flow_status_id=flow_status_id,
#                   success_no=stellar_hash,
#                   status='1',
#                   sign=sign_name,
#                   rand_string=rand_string
#                   )
#     print '111', params
#     response = requests.post(url, data=params).json()
#     # # response = {'code': 200}
#     # # ret = response.get('code')
#     print '2222', response
#     if response.get('code') == 200:
#         # 请求php接口成功
#         # print '**************', stellar_hash
#         if is_success:
#             # order = OrderDetail()
#             try:
#                 order = OrderDetail()
#                 order.query.filter_by(orders=flow_status_id).update(
#                     {'hash': str(stellar_hash), 'pay_status': 3, 'status': 1})
#                 # order.hash = hash
#                 # order.pay_status = 3
#                 # order.status = 1
#                 # order = OrderDetail(hash=hash,status=1, pay_status=3)
#                 # db.session.add_all([order])
#                 db.session.commit()
#             except Exception as e:
#                 logging.error(str(e) + u'user:%s, coin_name:%s, amount:%s转账成功存入数据哭失败' % (users, coin_name, amount))
#                 return False, u'paydex 修改状态失败转账失败'
#             return True, u'转账成功'
#
#     if response.get('code') != 200:
#         # 请求php接口失败, celery 异步延时任务
#
#         return ta.time_task.apply_async((params, stellar_hash, is_success, users, coin_name, amount, response,
#                                                 flow_status_id), retry=True, retry_policy={
#             'max_retries': 3,
#             'interval_start': 0,
#             'interval_step': 0.2,
#             'interval_max': 0.2,
#         })
