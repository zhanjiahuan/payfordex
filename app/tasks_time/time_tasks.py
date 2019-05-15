# coding: utf-8

from celery import Celery

# app = Celery('paydex', borker='redis://127.0.0.1:6378/5')


from app.tasks_pay.main import app
@app.task(name='time_task')
def time_task(params, stellar_hash, is_success, pay_account_seed, coin_name, amount, response, flow_status_id):
    # ret = ask_php(params, stellar_hash, is_success, pay_account_seed, coin_name, amount, response, flow_status_id)
    # return ret
    pass
