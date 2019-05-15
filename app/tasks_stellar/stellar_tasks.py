# coding: utf-8

from celery import Celery

# app = Celery('paydex', borker='redis://127.0.0.1:6378/5')


from app.tasks_pay.main import app

@app.task(name='pay_stellar')
def pay_stellar(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,
                memo_oreder_id):
    # ret = setllar_bottom_pay(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed,
    #                    memo_oreder_id)
    # return ret
    pass
