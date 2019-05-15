# coding: utf-8

from celery import Celery

# app = Celery('paydex', borker='redis://127.0.0.1:6378/5')
from main import app

# @app.task(name='insert_tasks')
# def insert_tasks(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
#                  memo_oreder_id):
#     # ret = get_pay_info_mysql(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
#     #                          memo_oreder_id)
#     # return ret
#     pass



