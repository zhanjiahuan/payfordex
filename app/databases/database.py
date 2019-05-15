# coding: utf-8
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Shell, Manager
from datetime import datetime
# from app.constant import MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, PAYDEX_PYTOHN

app = Flask(__name__)


# # 设置链接数据库
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:mysql@127.0.0.1:3306/paydex_python'
# # 设置每次请求结束后会自动提交数据库中的改动
# app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# # 设置成 True，SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存， 如果不必要的可以禁用它。
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


# 链接配置数据库
class DBConfig(object):
    DEBUG = True

    # 链接配置 测试服
    SQLALCHEMY_DATABASE_URI = "mysql://root:K3zBlCk06Lka0w1y@47.52.130.34:4406/paydex"

    # SQLALCHEMY_DATABASE_URI = 'mysql://root:' + MYSQL_PASSWORD + '@' + MYSQL_HOST + ':' + MYSQL_PORT + '/' + PAYDEX_PYTOHN

    # 本地mysql
    # SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/paydex"

    # sqlalchemy跟踪数据库修改
    # SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # 设置成 True，SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存， 如果不必要的可以禁用它。
    # SQLALCHEMY_TRACK_MODIFICATIONS = True

    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 显示sql语句
    SQLALCHEMY_ECHO = True


# 配置信息
app.config.from_object(DBConfig)

# 实例化 创建数据库
db = SQLAlchemy(app)

#  创建manager 启动
manager = Manager(app)
manager.add_command('db',MigrateCommand)

# 第一个参数是Flask的实例，第二个参数是Sqlalchemy数据库实例
migrate = Migrate(app, db)

# manager是Flask-Script的实例，这条语句在flask-Script中添加一个db命令
manager.add_command('db', MigrateCommand)

'''
1. python database.py db init  #初始化迁移环境，只运行一次
2. python database.py db migrate -m'更新备注' #生成迁移文件，模型改变了就需要执行
3. python database.py db upgrade #模型对象的字段映射到数据库表中

4. python database.py db history #查看迁移版本的历史记录
5. python database.py db downgrade 版本号 #回到对应版本
'''


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


# 定义模型类-订单信息无异常数据
class OrderDetail(BaseModel, db.Model):
    # 表名 order
    __tablename__ = 'order'
    orders = db.Column(db.String(64), primary_key=True, unique=True, index=True)  # 订单号
    hash = db.Column(db.String(64), unique=True)  # stellar 哈希
    count_hash = db.Column(db.String(64), nullable=False)  # 计算哈希
    collect_account_public = db.Column(db.String(64), nullable=False)  # 收款账户公钥
    pay_account_seed = db.Column(db.String(256), nullable=False)  # 付款账号秘钥
    amount = db.Column(db.String(64), nullable=False)  # 金额,浮点数字符串
    coin_name = db.Column(db.String(64), nullable=False)  # 付款货币名称
    memo_oreder_id = db.Column(db.String(64), nullable=True)  # 转账备注
    ask_frequency = db.Column(db.Integer, nullable=True)  # 请求第几次成功
    merchant_private = db.Column(db.String(256), nullable=True)  # 商户的秘钥 用来扣取手续费
    fee = db.Column(db.String(64), nullable=True)  # 转账手续费
    status = db.Column(db.Integer, nullable=True)  # 1=转账成功 ， 2=转账失败 php状态
    pay_status = db.Column(db.Integer, nullable=True)  # 1,转账开始,2,转账失败,3转账成功　



# 底层假超时信息
class SteallarFalseOverTimeInfo(BaseModel, db.Model):
    # 表名
    __tablename__ = 'false_over_time_order'
    false_over_time_orders = db.Column(db.String(64), primary_key=True, unique=True, index=True)  # 订单号
    false_over_time_count_hash = db.Column(db.String(64), unique=True, index=True)  # 计算哈希
    false_over_time_status = db.Column(db.Integer, nullable=True)  # 1=转账成功,php接口成功 ， 2=转账成功,请求 php接口失败


# 底层真超时转账信息
class SteallarTrueOverTimeInfo(BaseModel, db.Model):
    # 表名
    __tablename__ = 'true_over_time_order'
    true_over_time_orders = db.Column(db.String(64), primary_key=True, unique=True, index=True)  # 订单号
    true_over_time__status = db.Column(db.Integer, nullable=True)  # 1=转账成功 ， 2=转账失败 处理成功了该状态为一
    true_over_time_public = db.Column(db.String(64), nullable=False)  # 收款账户公钥
    true_over_time_pay_account_seed = db.Column(db.String(64), nullable=False)  # 付款账号秘钥
    true_over_time_amount = db.Column(db.String(64), nullable=False)  # 金额,浮点数字符串
    true_over_time_coin_name = db.Column(db.String(64), nullable=False)  # 付款货币名称
    true_over_time_memo_oreder_id = db.Column(db.String(64), nullable=True)  # 转账备注

# 兑换币交易信息表
class ExchangeDetail(BaseModel,db.Model):
    __tablename__ = 'exchange'
    orders = db.Column(db.String(64), primary_key=True, unique=True, index=True)  # 订单号
    stellar_hash = db.Column(db.String(64), unique=True)  # stellar 哈希
    account_seed = db.Column(db.String(256), nullable=False) # 账户秘钥
    coin_name = db.Column(db.String(64), nullable=False) # 兑换币种/获取币种
    amount = db.Column(db.String(64), nullable=False) #兑换币种数量/获取币种数量
    fee = db.Column(db.String(64), nullable=False)  # 转账手续费
    pay_status = db.Column(db.Integer, nullable=True)  # 1,转账开始,2,转账失败,3转账成功　
    status = db.Column(db.Integer, nullable=True)  # 1=转账成功 ， 2=转账失败 php状态
    ask_frequency = db.Column(db.Integer, nullable=True)  # 请求第几次成功




if __name__ == '__main__':
    manager.run()