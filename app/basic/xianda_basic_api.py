# encoding=utf8


import logging
from werkzeug.security import check_password_hash, generate_password_hash
from app import redisService
from app.constant import *

from decimal import Decimal

from flask_restplus import Namespace, Resource
from stellar_base.operation import CreateAccount, ChangeTrust, Payment  # operation:操作
from stellar_base.keypair import Keypair
from stellar_base.horizon import Horizon

from app.tasks_pay.pay.tasks import pay_requests
from app.utils.code_msg import create_response, XDCodeMsg
from app.utils.stellar_tasks import *
from app.utils.xianda_resource import XDRequestParser
from app.utils.stellar import mnemonic_keypair
from app.utils.commons import str_num_to_decimal
from app.utils.stellar import *
from app.databases.database import OrderDetail, db, ExchangeDetail
# from app.databases.add_data import get_pay_info_mysql

from app.tasks_pay.pay import tasks
# from app.tasks_pay import pay_tasks
from app.utils.utils import utc_to_local
from app.utils.session_pool import SessionPool
from app.vres.sign_name import fun_var_kargs, decryptStellarSeed, random_str

sessions = SessionPool()
basic_ns = Namespace("basic_api", description="basic_api")


@basic_ns.route("/getAccount")  # 生成账户
class CreateStellarAccount(Resource):
    @basic_ns.doc(
        params={
            'rand_string': U'随机字符串',
            'sign': U'签名'
        },
        description=U'API:生成stellar账户\n'
                    U'mnemonic:助记词\n'
                    U'account:stellar公钥\n'
                    U'seed:stellar秘钥'
    )
    def get(self):
        parser_ = XDRequestParser()
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        rand_string = params.get('rand_string')
        sign = params.get('sign')

        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string, )
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 调用mnemonic_keypair 生成账户
        return create_response(XDCodeMsg.SUCCESS, data=mnemonic_keypair())


@basic_ns.route("/addAccount")  # 激活接口
class CreateStellarAddAccount(Resource):
    @basic_ns.doc(
        params={
            'destination': U'激活stellar地址',
            'amount': U'金额,浮点数字符串',
            'source': U'付款账户seed',
            'rand_string': U'随机字符串',
            'sign': U'签名'

        },
        description=U'API:激活stellar账户\n'
                    U'钱很多账户：SDZPDZE4H5HCNR5RH2C6T32ZNORC6IQXLB6SQMJN6PVVSSMP5BCZIB2Z'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("destination", type=str, required=True)
        parser_.add_argument("amount", type=str, required=True)
        parser_.add_argument("source", type=str, required=True)
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        destination = params.get("destination")
        amount = params.get("amount")
        source = params.get("source")
        rand_string = params.get('rand_string')
        sign = params.get('sign')

        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string,
                                  source=source,
                                  amount=amount,
                                  destination=destination)
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 密钥校验
        deResult = decryptStellarSeed(source)
        if isinstance(deResult, XDCodeMsg.CodeMsg):
            return create_response(deResult)
        source = deResult

        # 检查输入金额是否有效
        amount = str_num_to_decimal(amount)
        if amount is None:
            return create_response(XDCodeMsg.CodeMsg(1200, U'错误的金额,小数位最多7位'))

        # 激活金额最小值，默认1可在constant设置
        if amount < Decimal(10):  # Decimal 转化成十进制 进行比较大小
            return create_response(XDCodeMsg.CodeMsg(1201, U'金额不得小于{}'.format('1')))

        # 账户是否合法
        if not check_stellar_account(destination):
            return create_response(XDCodeMsg.CodeMsg(1202, U'待激活账户非法'))

        # 检查待激活账户是否已近激活
        sequence = stellar_account_info(stellar_account=destination)[0]
        # print ('=>=>=>=>=>=>=>=>=>=>=>=>=>=>', sequence)
        if sequence is not None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'账户已激活'))

        try:
            source_keypair = Keypair.from_seed(source)
        except:
            return create_response(XDCodeMsg.CodeMsg(1205, U'无效付款账户'))

        # 获取该账户余额列表
        source_sequence, source_balance = stellar_account_info(source_keypair.address())
        if source_balance is None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'付款账户未激活'))

        native_balance = source_balance[len(source_balance) - 1]['balance']
        native_balance = Decimal(native_balance)

        if native_balance <= amount:
            return create_response(XDCodeMsg.CodeMsg(1205, U'余额不足'))

        # 构建stellar激活账户事物
        ops = list()
        op = CreateAccount(dict(destination=destination, starting_balance=str(amount)))
        ops.append(op)
        memo = U'激活账户'
        is_success, ret = create_envelope_submit(source_keypair, source_sequence, memo, ops)
        if not is_success:
            return create_response(XDCodeMsg.CodeMsg(1206, U'激活失败，账户负债过高'))
        return create_response(XDCodeMsg.SUCCESS, data=ret)


@basic_ns.route("/getAccountInfo")  # 查询测试账户资产
class AccountInfo(Resource):
    @basic_ns.doc(
        params={
            'account_address': U'stellar地址,',
            'rand_string': U'随机字符串',
            'sign': U'签名'
        },
        description=U'查詢用戶资产\n'
                    U'例如：GAOOAIVQNC4HLURYSUNPY3N3JGZHR5CHG4AHYZPSL5SCY5TCBHEFCXDB\n'
                    U'account_address: 必填'
    )
    def get(self):
        parser_ = XDRequestParser()
        parser_.add_argument("account_address", type=str, required=True)
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        account_address = params.get("account_address")
        rand_string = params.get('rand_string')
        sign = params.get('sign')

        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string,
                                  account_address=account_address)
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 账户是否合法
        if not check_stellar_account(account_address):
            return create_response(XDCodeMsg.CodeMsg(1202, U'非法账户'))

        # 3.1收款账户是否为有效账户
        if not check_stellar_account(account_address):
            return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户无效'))

        # 账户是否激活
        sequence, balances = stellar_account_info(account_address)
        if balances is None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'账户未激活'))

        return create_response(XDCodeMsg.SUCCESS, data=balances)


@basic_ns.route("/getAccountInfo/test")  # 查询测试账户资产
class AccountInfo(Resource):
    @basic_ns.doc(
        params={
            'account_address': U'stellar地址,',
            # 'rand_string': U'随机字符串',
            # 'sign': U'签名'
        },
        description=U'查詢用戶资产\n'
                    U'例如：GAOOAIVQNC4HLURYSUNPY3N3JGZHR5CHG4AHYZPSL5SCY5TCBHEFCXDB\n'
                    U'account_address: 必填'
    )
    def get(self):
        parser_ = XDRequestParser()
        parser_.add_argument("account_address", type=str, required=True)
        # parser_.add_argument('rand_string', type=str, required=True)
        # parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        account_address = params.get("account_address")
        # rand_string = params.get('rand_string')
        # sign = params.get('sign')

        # 验证签名
        # sign_name = fun_var_kargs(rand_string=rand_string,
        #                           account_address=account_address)
        # if sign_name != sign:
        #     return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 账户是否合法
        if not check_stellar_account(account_address):
            return create_response(XDCodeMsg.CodeMsg(1202, U'非法账户'))

        # 3.1收款账户是否为有效账户
        if not check_stellar_account(account_address):
            return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户无效'))

        # 账户是否激活
        sequence, balances = stellar_account_info(account_address)
        if balances is None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'账户未激活'))

        return create_response(XDCodeMsg.SUCCESS, data=balances)


@basic_ns.route("/payData")  # 转账接口
class PayData(Resource):
    @basic_ns.doc(
        params={
            'collect_account_public': u'收款账户公钥',
            'amount': u'金额,浮点数字符串',
            'coin_name': u'付款货币名称',
            'memo_oreder_id': u"转账备注",
            'pay_account_seed': u'付款账户密钥',
            'flow_status_id': u'转账订单号',
            'rand_string': U'随机字符串',
            'sign': U'签名',
            'merchant_private': U'商户私钥',
            'fee': U'转账手续费',

        },
        description=u'转账接口\n'
                    U'钱很多账户：SDZPDZE4H5HCNR5RH2C6T32ZNORC6IQXLB6SQMJN6PVVSSMP5BCZIB2Z'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("collect_account_public", type=str, required=True)
        parser_.add_argument("amount", type=str, required=True)
        parser_.add_argument("coin_name", type=str, required=True)
        parser_.add_argument("memo_oreder_id", type=unicode, required=False)
        parser_.add_argument("pay_account_seed", type=str, required=True)
        parser_.add_argument("flow_status_id", type=str, required=True)
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)
        parser_.add_argument('merchant_private', type=str, required=False)
        parser_.add_argument('fee', type=str, required=False)

        params = parser_.parse_args()
        collect_account_public = params.get("collect_account_public")
        amount = params.get("amount")
        coin_name = params.get("coin_name")
        memo_oreder_id = params.get("memo_oreder_id")
        pay_account_seed = params.get("pay_account_seed")
        flow_status_id = params.get("flow_status_id")
        rand_string = params.get('rand_string')
        sign = params.get('sign')
        merchant_private = params.get('merchant_private')
        fee = params.get('fee')

        if memo_oreder_id is None and memo_oreder_id[-4:] == 'true':
            # 检验是否从true_over_time_order（请求底层真超时）表中拿出的数据
            try:
                user = Keypair.from_seed(pay_account_seed)
            except:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))

            sequence, user_balances = stellar_account_info(user.address().decode(encoding='utf-8'))

            # 切片取出原始备注
            memo_oreder_id = memo_oreder_id.split(":")[0]
            if len(memo_oreder_id) <= 0:
                # 添加默认备注
                memo_oreder_id = u'用户发起转账'
        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string,
                                  collect_account_public=collect_account_public,
                                  amount=amount,
                                  coin_name=coin_name,
                                  memo_oreder_id=memo_oreder_id,
                                  pay_account_seed=pay_account_seed,
                                  flow_status_id=flow_status_id,
                                  merchant_private=merchant_private,
                                  fee=fee,
                                  )
        print sign_name,'11111',sign
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 密钥校验
        deResult = decryptStellarSeed(pay_account_seed)
        if isinstance(deResult, XDCodeMsg.CodeMsg):
            return create_response(deResult)
        pay_account_seed = deResult
        # 手续费商户秘钥校验
        if merchant_private:
            deResult_fee = decryptStellarSeed(merchant_private)
            if isinstance(deResult_fee, XDCodeMsg.CodeMsg):
                return create_response(deResult_fee)
            merchant_private = deResult_fee

        # 参数校验
        if memo_oreder_id == None:
            memo_oreder_id = '用户发起转账'
        if len(memo_oreder_id) > 28:
            return create_response(XDCodeMsg.CodeMsg(1202, u'备注最长28个字符'))

        # 2.校验付款数量,stellar底层只接受最多7位小数
        amount = str_num_to_decimal(amount)
        if amount is None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款数量无效'))

        # 3.校验收款账户是否有效
        # 3.1收款账户是否为有效账户
        if not check_stellar_account(collect_account_public):
            return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户无效'))

        # 4.校验付款账户
        # 4.1校验付款账户是否合法
        try:
            user = Keypair.from_seed(pay_account_seed)
            # print(user)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))

        # 获取用户余额序列号 获取付款账户stellar信息判断账户是否激活
        sequence, user_balances = stellar_account_info(user.address().decode(encoding='utf-8'))

        collect_account_sequence, collect_account_balances = stellar_account_info(collect_account_public)

        # 参数校验
        if coin_name == PAYDEX_CODE:
            # 3.3收款账户未激活
            if not collect_account_sequence:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in collect_account_balances:
                asset_code = asset.get('asset_code', PAYDEX_CODE)
                if asset_code == coin_name:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', PAYDEX_CODE)

                # 条件都满足时
                if asset_code == coin_name:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))
        else:

            # 3.3收款账户未激活
            if not collect_account_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in collect_account_balances:
                asset_code = asset.get('asset_code', 'VTOKEN')
                asset_issuer = asset.get('asset_issuer')
                if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.2获取付款账户stellar信息判断账户是否激活,是否信任付款货币
            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', 'VTOKEN')
                # 信任的货币是否时统一法定账户
                asset_issuer = asset.get('asset_issuer')
                # 条件都满足时
                if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))

        if pay_asset_balance <= amount:  # todo:需要考虑手续费
            return create_response(XDCodeMsg.CodeMsg(1202, u'{}余额不足'.format(coin_name)))

        # 查询数据库订单号是否存在
        ret = OrderDetail.query.filter(OrderDetail.orders == flow_status_id).first()

        if ret is not None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'重复的订单号'))
        amount = str(amount)
        opts = list()
        opt = Payment(dict(
            destination=collect_account_public,
            asset=Asset(coin_name, COINS_ISSUER),
            amount=str(amount)
        ))
        opts.append(opt)
        # 计算哈希
        count_hash = create_envelope(user, sequence, memo_oreder_id, opts)
        # 私钥加密
        pay_account_seed_enc = generate_password_hash(collect_account_public)
        if merchant_private:
            merchant_private_enc = generate_password_hash(merchant_private)
        try:
            # # 转账信息存入mysql
            if merchant_private:
                order = OrderDetail(orders=flow_status_id,
                                    count_hash=count_hash,
                                    pay_account_seed=pay_account_seed_enc,
                                    collect_account_public=collect_account_public,
                                    amount=amount,
                                    coin_name=coin_name,
                                    memo_oreder_id=memo_oreder_id,
                                    pay_status=1,
                                    merchant_private=merchant_private_enc,
                                    fee=fee
                                    )

                db.session.add_all([order])
                db.session.commit()

            else:
                order = OrderDetail(orders=flow_status_id,
                                    count_hash=count_hash,
                                    pay_account_seed=pay_account_seed_enc,
                                    collect_account_public=collect_account_public,
                                    amount=amount,
                                    coin_name=coin_name,
                                    memo_oreder_id=memo_oreder_id,
                                    pay_status=1,
                                    )

                db.session.add_all([order])
                db.session.commit()
        except Exception as e:
            logging.error(e)
            return create_response(XDCodeMsg.CodeMsg(1202, u'信息存入数据库失败'))

        try:
            pay_requests.delay(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
                               memo_oreder_id, merchant_private, fee)
            # pay_requests(collect_account_public, amount, coin_name, flow_status_id, pay_account_seed, sequence,
            #                    memo_oreder_id, merchant_private, fee)

        except:
            return create_response(XDCodeMsg.CodeMsg(1202, U'异步回调通知失败'))


        return create_response(XDCodeMsg.CodeMsg(200, U'转账参数获取成功,开始异步任务'))




@basic_ns.route("/payGiro")  # 测试转账接口
class PayData(Resource):
    @basic_ns.doc(
        params={
            'collect_account_public': u'收款账户公钥',
            'amount': u'金额,浮点数字符串',
            'coin_name': u'付款货币名称',
            'memo_oreder_id': u"转账备注",
            'pay_account_seed': u'付款账户密钥',
        },
        description=u'转账接口\n'
                    U'钱很多账户：SDZPDZE4H5HCNR5RH2C6T32ZNORC6IQXLB6SQMJN6PVVSSMP5BCZIB2Z'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("collect_account_public", type=str, required=True)
        parser_.add_argument("amount", type=str, required=True)
        parser_.add_argument("coin_name", type=str, required=True)
        parser_.add_argument("memo_oreder_id", type=str, required=False)
        parser_.add_argument("pay_account_seed", type=str, required=True)

        params = parser_.parse_args()
        collect_account_public = params.get("collect_account_public")
        amount = params.get("amount")
        coin_name = params.get("coin_name")
        memo_oreder_id = params.get("memo_oreder_id")
        pay_account_seed = params.get("pay_account_seed")

        # 参数校验
        if memo_oreder_id == None:
            memo_oreder_id = '用户发起转账'
        if len(memo_oreder_id) > 28:
            return create_response(XDCodeMsg.CodeMsg(1202, u'备注最长28个字符'))

        # 2.校验付款数量,stellar底层只接受最多7位小数
        amount = str_num_to_decimal(amount)
        if amount is None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款数量无效'))

        # 3.校验收款账户是否有效
        # 3.1收款账户是否为有效账户
        if not check_stellar_account(collect_account_public):
            return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户无效'))

        # 4.校验付款账户
        # 4.1校验付款账户是否合法
        try:
            user = Keypair.from_seed(pay_account_seed)
            # print(user)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))

        # 获取用户余额序列号 获取付款账户stellar信息判断账户是否激活
        sequence, user_balances = stellar_account_info(user.address().decode(encoding='utf-8'))

        # 参数校验
        if coin_name == PAYDEX_CODE:
            # 3.3收款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in user_balances:
                asset_code = asset.get('asset_code', PAYDEX_CODE)
                if asset_code == coin_name:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.校验付款账户
            # 4.1校验付款账户是否合法
            try:
                user = Keypair.from_seed(pay_account_seed)
                # print(user)
            except:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))
            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', PAYDEX_CODE)

                # 条件都满足时
                if asset_code == coin_name:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))
        else:

            # 3.3收款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in user_balances:
                asset_code = asset.get('asset_code', 'VTOKEN')
                asset_issuer = asset.get('asset_issuer')
                if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.2获取付款账户stellar信息判断账户是否激活,是否信任付款货币
            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', 'VTOKEN')
                # 信任的货币是否时统一法定账户
                asset_issuer = asset.get('asset_issuer')
                # 条件都满足时
                if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))

        if pay_asset_balance <= amount:  # todo:需要考虑手续费
            return create_response(XDCodeMsg.CodeMsg(1202, u'{}余额不足'.format(coin_name)))

        # 5参数校验完毕,组建付款操作
        opts = list()
        opt = Payment(dict(
            destination=collect_account_public,
            asset=Asset.native() if coin_name == PAYDEX_CODE else Asset(coin_name, COINS_ISSUER),
            amount=str(amount)
        ))
        opts.append(opt)

        is_success, ret = create_envelope_submit(user, sequence, memo_oreder_id, opts)
        if not is_success:
            return create_response(XDCodeMsg.CodeMsg(1202, u'请求超时,请稍后在试.'))
        return create_response(XDCodeMsg.SUCCESS, data=ret)


@basic_ns.route("/pay")  # php充值接口
class PayData(Resource):
    @basic_ns.doc(
        params={
            'collect_account_public': u'收款账户公钥',
            'amount': u'金额,浮点数字符串',
            'coin_name': u'付款货币名称',
            'memo_oreder_id': u"转账备注",
            'pay_account_seed': u'付款账户密钥',
            'rand_string': U'随机字符串',
            'sign': U'签名',
        },
        description=u'转账接口\n'
                    U'钱很多账户：SDZPDZE4H5HCNR5RH2C6T32ZNORC6IQXLB6SQMJN6PVVSSMP5BCZIB2Z'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("collect_account_public", type=str, required=True)
        parser_.add_argument("amount", type=str, required=True)
        parser_.add_argument("coin_name", type=str, required=True)
        parser_.add_argument("memo_oreder_id", type=str, required=False)
        parser_.add_argument("pay_account_seed", type=str, required=True)
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        collect_account_public = params.get("collect_account_public")
        amount = params.get("amount")
        coin_name = params.get("coin_name")
        memo_oreder_id = params.get("memo_oreder_id")
        pay_account_seed = params.get("pay_account_seed")
        rand_string = params.get('rand_string')
        sign = params.get('sign')

        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string,
                                  collect_account_public=collect_account_public,
                                  amount=amount,
                                  coin_name=coin_name,
                                  memo_oreder_id=memo_oreder_id,
                                  pay_account_seed=pay_account_seed, )
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 密钥校验
        deResult = decryptStellarSeed(pay_account_seed)
        if isinstance(deResult, XDCodeMsg.CodeMsg):
            return create_response(deResult)
        pay_account_seed = deResult
        # 参数校验
        if memo_oreder_id == None:
            memo_oreder_id = '用户发起转账'
        if len(memo_oreder_id) > 28:
            return create_response(XDCodeMsg.CodeMsg(1202, u'备注最长28个字符'))

        # 2.校验付款数量,stellar底层只接受最多7位小数
        amount = str_num_to_decimal(amount)
        if amount is None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款数量无效'))

        # 3.校验收款账户是否有效
        # 3.1收款账户是否为有效账户
        if not check_stellar_account(collect_account_public):
            return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户无效'))

        # 4.校验付款账户
        # 4.1校验付款账户是否合法
        try:
            user = Keypair.from_seed(pay_account_seed)
            # print(user)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))

        # 获取用户余额序列号 获取付款账户stellar信息判断账户是否激活
        sequence, user_balances = stellar_account_info(user.address().decode(encoding='utf-8'))

        # 参数校验
        if coin_name == PAYDEX_CODE:
            # 3.3收款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in user_balances:
                asset_code = asset.get('asset_code', PAYDEX_CODE)
                if asset_code == coin_name:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.校验付款账户
            # 4.1校验付款账户是否合法
            try:
                user = Keypair.from_seed(pay_account_seed)
                # print(user)
            except:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))
            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', PAYDEX_CODE)

                # 条件都满足时
                if asset_code == coin_name:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))
        else:

            # 3.3收款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in user_balances:
                asset_code = asset.get('asset_code', 'VTOKEN')
                asset_issuer = asset.get('asset_issuer')
                if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.2获取付款账户stellar信息判断账户是否激活,是否信任付款货币
            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', 'VTOKEN')
                # 信任的货币是否时统一法定账户
                asset_issuer = asset.get('asset_issuer')
                # 条件都满足时
                if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))

        if pay_asset_balance <= amount:  # todo:需要考虑手续费
            return create_response(XDCodeMsg.CodeMsg(1202, u'{}余额不足'.format(coin_name)))

        # 5参数校验完毕,组建付款操作
        opts = list()
        opt = Payment(dict(
            destination=collect_account_public,
            asset=Asset.native() if coin_name == PAYDEX_CODE else Asset(coin_name, COINS_ISSUER),
            amount=str(amount)
        ))
        opts.append(opt)

        is_success, ret = create_envelope_submit(user, sequence, memo_oreder_id, opts)
        if not is_success:
            return create_response(XDCodeMsg.CodeMsg(1202, u'请求超时,请稍后在试.'))
        return create_response(XDCodeMsg.SUCCESS, data=ret)


@basic_ns.route("/user/addAsset")  # 添加信任
class TrustAsset(Resource):
    @basic_ns.doc(
        params={
            'user_seed': U'用户秘钥',
            'coin_name': U'货币名字',
            'rand_string': U'随机字符串',
            'sign': U'签名'
        },
        description=U'用户资产信任')
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("user_seed", type=str, required=True)
        parser_.add_argument("coin_name", type=str, required=True)
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        user_seed = params.get("user_seed")
        coin_name = params.get("coin_name")
        rand_string = params.get('rand_string')
        sign = params.get('sign')

        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string,
                                  coin_name=coin_name,
                                  user_seed=user_seed, )

        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))
        # 密钥校验
        deResult = decryptStellarSeed(user_seed)
        if isinstance(deResult, XDCodeMsg.CodeMsg):
            return create_response(deResult)
        user_seed = deResult

        # 获取用户余额，判断用户是否激活
        try:
            user_balances = pay_object(user_seed)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, U'非法账户,请重新输入'))

        # 如果货币名为原生币
        if coin_name == PAYDEX_CODE:
            return create_response(XDCodeMsg.CodeMsg(1001, U'资产已信任'))

        if not check_stellar_account(user_balances):
            return create_response(XDCodeMsg.CodeMsg(1202, U'待激活账户非法'))

        # 调用方法获取序列号 和 余额
        sequence, balances = stellar_account_info(user_balances)
        # print ('=====================================', balances)
        # if sequence is not None:
        if balances is None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'账户未激活'))

        try:
            source_keypair = Keypair.from_seed(user_seed)
        except:
            return create_response(XDCodeMsg.CodeMsg(1205, U'无效账户'))

        # 组件事务提交
        ops = list()
        asset = asset_obj(coin_name)
        op = ChangeTrust(dict(asset=asset))
        ops.append(op)
        memo = '信任资产'
        # 调用方法 create_envelope_submit 事务封包,并提交
        is_success, msg = create_envelope_submit(source_keypair, sequence, memo, ops)
        if not is_success:
            print (msg)
            return create_response(XDCodeMsg.CodeMsg(1005, U'{}不足'.format(PAYDEX_CODE)))
        return create_response(XDCodeMsg.SUCCESS, data=msg)


@basic_ns.route("/GetAccount")  # 生成账户并且激活
class EstablishAccount(Resource):
    @basic_ns.doc(
        params={
            'rand_string': U'随机字符串',
            'sign': U'签名'
        },
        description=U'API:生成stellar账户\n'
                    U'mnemonic:助记词\n'
                    U'account:stellar公钥\n'
                    U'seed:stellar秘钥'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument('rand_string', type=str, required=True)
        parser_.add_argument('sign', type=str, required=True)

        params = parser_.parse_args()
        rand_string = params.get('rand_string')
        sign = params.get('sign')

        # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string, )
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        stellar_account = mnemonic_keypair()
        destination = stellar_account.get('account')
        amount = str(10000)
        source = COINS_SEED
        # 检查输入金额是否有效
        amount = str_num_to_decimal(amount)
        if amount is None:
            return create_response(XDCodeMsg.CodeMsg(1200, U'错误的金额,小数位最多7位'))

        # 激活金额最小值，默认1可在constant设置
        if amount < Decimal(10):  # Decimal 转化成十进制 进行比较大小
            return create_response(XDCodeMsg.CodeMsg(1201, U'金额不得小于{}'.format('1')))

        # 账户是否合法
        if not check_stellar_account(destination):
            return create_response(XDCodeMsg.CodeMsg(1202, U'待激活账户非法'))

        # 检查待激活账户是否已近激活
        sequence = stellar_account_info(stellar_account=destination)[0]
        if sequence is not None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'账户已激活'))

        try:
            source_keypair = Keypair.from_seed(source)
        except:
            return create_response(XDCodeMsg.CodeMsg(1205, U'无效付款账户'))

        # 获取该账户余额列表
        source_sequence, source_balance = stellar_account_info(source_keypair.address())
        if source_balance is None:
            return create_response(XDCodeMsg.CodeMsg(1203, U'付款账户未激活'))

        native_balance = source_balance[len(source_balance) - 1]['balance']
        native_balance = Decimal(native_balance)

        if native_balance <= amount:
            return create_response(XDCodeMsg.CodeMsg(1205, U'余额不足'))

        # 构建stellar激活账户事物
        ops = list()
        op = CreateAccount(dict(destination=destination, starting_balance=str(amount)))
        ops.append(op)
        memo = U'激活账户'
        is_success, ret = create_envelope_submit(source_keypair, source_sequence, memo, ops)
        if not is_success:
            return create_response(XDCodeMsg.CodeMsg(1206, U'激活失败，账户负债过高'))
        return create_response(XDCodeMsg.SUCCESS, data=stellar_account)


# @basic_ns.route("/issuing_asset")
# class Issuing_Asset(Resource):
#     @basic_ns.doc(
#         params={
#             'amount': u'数量',
#             'coin_name': u'资产名',
#             'issuer_assets_seed': u'资产发行密钥',
#             'rand_string': U'随机字符串',
#             'sign': U'签名'
#         },
#         description=U'API:发币接口\n'
#
#     )
#     def post(self):
#         parser_ = XDRequestParser()
#         parser_.add_argument("issuer_assets_seed", type=str, required=True)
#         parser_.add_argument("amount", type=str, required=True)
#         parser_.add_argument("coin_name", type=str, required=True)
#         parser_.add_argument('rand_string', type=str, required=True)
#         parser_.add_argument('sign', type=str, required=True)
#
#         params = parser_.parse_args()
#         coin_name = params.get("coin_name")
#         amount = params.get("amount")
#         issuer_assets_seed = params.get("issuer_assets_seed")
#         rand_string = params.get('rand_string')
#         sign = params.get('sign')
#
#         # 秘钥解密
#         # issuer_assets_seed = decryptStellarSeed(issuer_assets_seed)
#
#         # 验证签名
#         sign_name = fun_var_kargs(rand_string=rand_string,
#                                   coin_name=coin_name,
#                                   amount=amount,
#                                   issuer_assets_seed=issuer_assets_seed,
#                                   )
#         if sign_name != sign:
#             return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))
#
#         # 密钥校验
#         deResult = decryptStellarSeed(issuer_assets_seed)
#         if isinstance(deResult, XDCodeMsg.CodeMsg):
#             return create_response(deResult)
#         issuer_assets_seed = deResult
#
#         # 货币名校验
#         if len(coin_name) > 12:
#             return create_response(XDCodeMsg.CodeMsg(1001, U'货币名称过长'))
#
#         # 发行数量校验
#         try:
#             amount = Decimal(amount)
#         except:
#             return create_response(XDCodeMsg.CodeMsg(1001, U'发行数量有误'))
#         if amount <= 0:
#             return create_response(XDCodeMsg.CodeMsg(1001, U'发行数量必须大于0'))
#
#         try:
#             # 资产发行 对象
#             source_keypair_issue = Keypair.from_seed(issuer_assets_seed)
#         except:
#             return create_response(XDCodeMsg.CodeMsg(1205, U'发型币种账户无效'))
#
#         try:
#             # 资产发行序列号，　余额
#             sequence_issue, balances_issue = stellar_account_info(source_keypair_issue.address())
#         except Exception:
#             return create_response(XDCodeMsg.CodeMsg(1205, U'发型币种账户无效'))
#         try:
#             source_keypair_base = Keypair.from_seed(COINS_SEED)
#         except Exception:
#             return create_response(XDCodeMsg.CodeMsg(1205, U'无效账户'))
#
#         try:
#             # 统一账户序列号，　余额
#             sequence_base, balances_base = stellar_account_info(source_keypair_base.address())
#         except Exception:
#             return create_response(XDCodeMsg.CodeMsg(1205, U'发型币种账户无效'))
#
#         if sequence_base is None or sequence_issue is None:
#             return create_response(XDCodeMsg.CodeMsg(1205, U'请确认账户是否激活'))
#
#         # 信任操作
#         ops = list()
#         asset = asset_obj(coin_name)
#         op = ChangeTrust(dict(asset=asset))
#         ops.append(op)
#         memo = '信任资产'
#         # 调用方法 create_envelope_submit 事务封包,并提交
#         is_success, msg = create_envelope_submit(source_keypair_issue, sequence_issue, memo, ops)
#
#         if not is_success:
#             return create_response(XDCodeMsg.CodeMsg(1005, U'{}不足'.format(PAYDEX_CODE)))
#
#         # 付款操作
#         opts = list()
#         opt = Payment(dict(
#             destination=source_keypair_base.address(),
#             asset=Asset.native() if coin_name == PAYDEX_CODE else Asset(coin_name, COINS_ISSUER),
#             amount=str(amount)
#         ))
#         opts.append(opt)
#         memos = '转账'
#         is_success, ret = create_envelope_submit(source_keypair_base, sequence_base, memos, opts)
#         if not ret:
#             return create_response(XDCodeMsg.CodeMsg(1202, u'转账失败,is_success值为｛｝'.format(ret)))
#
#         return create_response(XDCodeMsg.SUCCESS, data=ret)


@basic_ns.route("/issuing_asset")  # 后台资产发行接口
class IssuingAsset(Resource):
    @basic_ns.doc(
        params={
            'coin_name': u'资产名',
            'amount': u'数量',
            'issuer_assets_seed': u'资产发行密钥',
            'rand_string': u"随机字符串",
            'sign': U'簽名'
        },
        description=U'资产发行'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("coin_name", type=str, required=True)
        parser_.add_argument("amount", type=str, required=True)
        parser_.add_argument("issuer_assets_seed", type=str, required=True)
        parser_.add_argument("rand_string", type=str, required=True)
        parser_.add_argument("sign", type=str, required=True)

        params = parser_.parse_args()
        coin_name = params.get('coin_name')
        amount = params.get('amount')
        issuer_assets_seed = params.get('issuer_assets_seed')
        rand_string = params.get("rand_string")
        sign = params.get("sign")

        # 签名
        python_sign = fun_var_kargs(rand_string=rand_string,
                                    coin_name=coin_name,
                                    amount=amount,
                                    issuer_assets_seed=issuer_assets_seed)
        if sign != python_sign:
            return create_response(XDCodeMsg.CodeMsg(1209, "签名不相等"))

        # 密钥校验
        deResult = decryptStellarSeed(issuer_assets_seed)
        if isinstance(deResult, XDCodeMsg.CodeMsg):
            return create_response(deResult)
        issuer_assets_seed = deResult

        # 货币名校验
        if len(coin_name) > 12:
            return create_response(XDCodeMsg.CodeMsg(1001, U'货币名称过长'))

        # 发行数量校验
        try:
            amount = Decimal(amount)
        except:
            return create_response(XDCodeMsg.CodeMsg(1001, U'发行数量有误'))
        if amount <= 0:
            return create_response(XDCodeMsg.CodeMsg(1001, U'发行数量必须大于0'))
        # amount = format(amount,'.7f')   # 发行数量最多7位小数
        try:
            seed_obj = Keypair.from_seed(issuer_assets_seed)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))
        # 资产发行账户验证
        # 1.密钥验证
        # 获取财务账户资产列表
        sequence, balances = stellar_account_info(seed_obj.address().decode(encoding='utf-8'))
        if not sequence:
            return create_response(XDCodeMsg.CodeMsg(1001, U'资产发行账户错误'))

        try:
            user = Keypair.from_seed(issuer_assets_seed)
            # print(user)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))

        # 2.账户公钥验证
        # 4.校验付款账户
        # 4.1校验付款账户是否合法
        if user.address().decode() != COINS_ISSUER:
            return create_response(XDCodeMsg.CodeMsg(1001, U'资产发行账户错误'))

        # consul获取财务密钥
        finania_seed = COIN_SEED
        try:
            finania_kp = Keypair.from_seed(finania_seed)  # Keypair 对象
        except:
            return create_response(XDCodeMsg.CodeMsg(1001, U'请检查财务账户是否正确'))

        # 获取财务账户资产列表
        sequence_finance, balances_finance = stellar_account_info(finania_kp.address())
        if not sequence:
            return create_response(XDCodeMsg.CodeMsg(1001, U'财务账户未激活'))

        asset_balance = 0  # 财务账户资产持有量
        asset_limit = Decimal('922337203685.4775807')  # 财务账户资产最大持有量
        is_issue = False  # 货币已发行
        for asset in balances:
            asset_code = asset.get('asset_code')
            asset_issuer = asset.get('asset_issuer')
            if asset_code == coin_name and asset_issuer == COINS_ISSUER:
                is_issue = True  # 货币未发行
                asset_balance = Decimal(asset.get('balance'))
                break

        # stellar转账
        # 1.再次发行,不需要信任,统一账户直接转账
        if is_issue:
            if amount + asset_balance > asset_limit:
                return create_response(XDCodeMsg.CodeMsg(1001, U'财务账户持有资产超出限制'))

        # 2.第一次发行,财务账户信任，在转账
        else:
            if amount > asset_limit:
                return create_response(XDCodeMsg.CodeMsg(1001, U'发行数量超出限制'))
            # 财务账户信任发行货币
            # 组件事务提交
            trust_ops = list()
            op = ChangeTrust(dict(asset=Asset(coin_name, COINS_ISSUER)))
            trust_ops.append(op)
            memo = '信任资产'
            # is_success, msg = finania_account.create_envelope_submit(finania_kp, finania_seq, memo, trust_ops)
            is_success, ret = create_envelope_submit(finania_kp, sequence_finance, memo, trust_ops)
            if not is_success:
                return create_response(XDCodeMsg.CodeMsg(1001, U'发行货币失败，请稍后再试'))

        # 3.统一账户进行转账
        pay_ops = list()
        memo = u'{}转账'.format(coin_name)
        op = Payment({
            'destination': finania_kp.address(),
            'asset': Asset(coin_name, COINS_ISSUER),
            'amount': format(amount, '.7f')
        })
        pay_ops.append(op)
        is_success, ret = create_envelope_submit(seed_obj,
                                                 sequence, memo, pay_ops)
        if not is_success:
            return create_response(XDCodeMsg.CodeMsg(1001, U'发行货币失败，请稍后再试'), data=ret)

        return create_response(XDCodeMsg.SUCCESS, data=ret)


@basic_ns.route("/exchange")  # 兑换币接口
class ExChange(Resource):
    @basic_ns.doc(
        params={
            'exchange_account_seed': u'兑换用户秘钥',
            'exchange_coin_name': u'兑换币名',
            'exchange_amount': u'兑换数量',
            'get_coin_name': u'获取币名',
            'get_amount': u'获取数量',
            'fee_amount': u'手续费扣除数量',
            'flow_status_id': u'订单号',
            'rand_string': u"随机字符串",
            'sign': U'簽名'
        },
        description=U'兑换接口'
    )
    def post(self):
        parser_ = XDRequestParser()
        parser_.add_argument("exchange_account_seed", type=str, required=True)
        parser_.add_argument("exchange_coin_name", type=str, required=True)
        parser_.add_argument("exchange_amount", type=str, required=True)
        parser_.add_argument("get_coin_name", type=str, required=True)
        parser_.add_argument("get_amount", type=str, required=True)
        parser_.add_argument("fee_amount", type=str)
        parser_.add_argument("flow_status_id", type=str, required=True)
        parser_.add_argument("rand_string", type=str, required=True)
        parser_.add_argument("sign", type=str, required=True)

        params = parser_.parse_args()
        exchange_account_seed = params.get('exchange_account_seed')
        exchange_coin_name = params.get('exchange_coin_name')
        exchange_amount = params.get('exchange_amount')
        get_coin_name = params.get("get_coin_name")
        get_amount = params.get("get_amount")
        fee_amount = params.get('fee_amount')
        flow_status_id = params.get('flow_status_id')
        rand_string = params.get("rand_string")
        sign = params.get("sign")
        #
        # # 验证签名
        sign_name = fun_var_kargs(rand_string=rand_string,
                                  exchange_account_seed=exchange_account_seed,
                                  exchange_coin_name=exchange_coin_name,
                                  exchange_amount=exchange_amount,
                                  get_amount=get_amount,
                                  get_coin_name=get_coin_name,
                                  fee_amount=fee_amount,
                                  flow_status_id=flow_status_id, )
        if sign_name != sign:
            return create_response(XDCodeMsg.CodeMsg(1200, U'签名验证失败'))

        # 密钥校验
        deResult = decryptStellarSeed(exchange_account_seed)
        if isinstance(deResult, XDCodeMsg.CodeMsg):
            return create_response(deResult)
        exchange_account_seed = deResult

        # 2.校验付款数量,stellar底层只接受最多7位小数
        amount = str_num_to_decimal(exchange_amount)
        if amount is None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款数量无效'))

        get_amount = str_num_to_decimal(get_amount)
        if get_amount is None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款数量无效'))

        # 3.校验收款账户是否有效
        # 3.1收款账户是否为有效账户
        if not check_stellar_account(COIN_ISSUER):
            return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户无效'))

        # 4.校验付款账户
        # 4.1校验付款账户是否合法
        try:
            user = Keypair.from_seed(exchange_account_seed)
            # print(user)
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户无效'))

        # 获取用户余额序列号 获取付款账户stellar信息判断账户是否激活
        sequence, user_balances = stellar_account_info(user.address().decode(encoding='utf-8'))
        print user_balances

        collect_account_sequence, collect_account_balances = stellar_account_info(user.address())

        # 参数校验
        if exchange_coin_name == PAYDEX_CODE:
            # 3.3收款账户未激活
            if not collect_account_sequence:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in collect_account_balances:
                asset_code = asset.get('asset_code', PAYDEX_CODE)
                if asset_code == exchange_coin_name:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', PAYDEX_CODE)

                # 条件都满足时
                if asset_code == exchange_coin_name:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))
        else:

            # 3.3收款账户未激活
            if not collect_account_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款账户未激活'))
            # 3.4收款账户未信任收款货币
            is_trust = False  #
            for asset in collect_account_balances:
                asset_code = asset.get('asset_code', 'PAYDEX')
                asset_issuer = asset.get('asset_issuer')
                if asset_code == exchange_coin_name and asset_issuer == COINS_ISSUER:
                    is_trust = True
                    break
            if not is_trust:
                return create_response(XDCodeMsg.CodeMsg(1202, u'收款方未信任收款货币'))

            # 4.2获取付款账户stellar信息判断账户是否激活,是否信任付款货币
            # 4.3付款款账户未激活
            if not user_balances:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款账户未激活'))
            # 4.4付款账户未信任收款货币
            pay_asset_balance = None
            get_asset_balance = None
            for asset in user_balances:
                # 取出信任的的货币名
                asset_code = asset.get('asset_code', 'PAYDEX')
                # 信任的货币是否时统一法定账户
                asset_issuer = asset.get('asset_issuer')
                # 条件都满足时
                if asset_code == exchange_coin_name and asset_issuer == COINS_ISSUER:
                    pay_asset_balance = Decimal(asset.get('balance'))
                    break
                    # if asset_code == get_coin_name and asset_issuer == COINS_ISSUER:
                    #     pay_asset_balance = Decimal(asset.get('balance'))
                    #     break
            if pay_asset_balance is None:
                return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任付款货币'))

                # if get_asset_balance is None:
                #     return create_response(XDCodeMsg.CodeMsg(1202, u'付款方未信任想兑换的货币'))
        print pay_asset_balance,type(pay_asset_balance)
        print exchange_amount,type(exchange_amount)
        if pay_asset_balance < Decimal(exchange_amount):  # todo:需要考虑手续费
            return create_response(XDCodeMsg.CodeMsg(1202, u'{}余额不足'.format(exchange_coin_name)))

        # 查询数据库订单号是否存在
        ret = ExchangeDetail.query.filter(ExchangeDetail.orders == flow_status_id).first()

        if ret is not None:
            return create_response(XDCodeMsg.CodeMsg(1202, u'重复的订单号'))
        # 私钥加密
        exchange_account_seed_ecn = generate_password_hash(exchange_account_seed)
        orders = flow_status_id
        account_seed = exchange_account_seed_ecn
        coin_name = exchange_coin_name + "/" + get_coin_name
        amount = str(exchange_amount) + "/" + str(get_amount)
        fee = fee_amount if fee_amount!="0" else "0"
        try:
            # # 转账信息存入mysql
            exchange = ExchangeDetail(orders=orders,
                                      account_seed=account_seed,
                                      coin_name=coin_name,
                                      amount=amount,
                                      fee=fee,
                                      pay_status=1,)

            db.session.add_all([exchange])
            db.session.commit()
        except Exception as e:
            logging.error(e)
            return create_response(XDCodeMsg.CodeMsg(1202, u'信息存入数据库失败'))
        memo_oreder_id = "兑换"
        merchant_private = "兑换"
        collect_account_public = "兑换"
        try:
            # pay_requests(collect_account_public, amount, coin_name, orders, exchange_account_seed, sequence,
            #              memo_oreder_id, merchant_private, fee, )
            pay_requests.delay(collect_account_public, amount, coin_name, orders, exchange_account_seed, sequence,
                         memo_oreder_id, merchant_private, fee, )
        except:
            return create_response(XDCodeMsg.CodeMsg(1202, U'异步回调通知失败'))

        return create_response(XDCodeMsg.CodeMsg(200, U'兑换币参数获取成功,开始异步任务'))






# @basic_ns.route("/get_latest_all_blocks")
# class GetLatestAndAllBlocksInfoInterface(Resource):
#     @basic_ns.doc(params={'order': 'desc or asc', 'page_num': '填写now or paging_token的值',
#                           },
#                   description=u"根据输入参数获取最新区块信息或者获取所有区块信息\n可能的错误\n"
#                               u"122,page_size 无效\n123,page_num 或 order 无效")
#     def get(self):
#         parser_ = XDRequestParser()
#         parser_.add_argument("order", type=str, required=True)
#         parser_.add_argument("page_num", type=str, required=True)
#         params = parser_.parse_args()
#         order = params.get("order")
#         page_num = params.get("page_num")
#         blockinfo = self.getLatestBlocksInfo(20, order, page_num)
#         return create_response(XDCodeMsg.SUCCESS, data=blockinfo)
#
#     def getLatestBlocksInfo(self, page_size, order, page_num):
#         fail_data = None
#         if page_num == 'now':
#             try:
#                 print "redis"
#                 basicnfo = redisService.get('ledgersInfo')
#                 print 'basicnfo', basicnfo
#             except Exception as e:
#                 basicnfo = None
#                 logging.error(e)
#             if not basicnfo or basicnfo == '':
#                 basicnfos = getLatestBlocksInfos(page_size, order, page_num)
#                 if isinstance(basicnfos, XDCodeMsg):
#                     return basicnfos, fail_data
#                 return create_response(XDCodeMsg.SUCCESS, data=basicnfos)
#             return create_response(XDCodeMsg.SUCCESS, data=basicnfo)
#         # 如果redis没有数据则从网页获取
#         else:
#             basicnfos = getLatestBlocksInfos(page_size, order, page_num)
#             if isinstance(basicnfos, XDCodeMsg):
#                 return basicnfos, fail_data
#             return create_response(XDCodeMsg.SUCCESS, data=basicnfos)
#
#
# @basic_ns.route("/get_main_chain_info")
# class GetMainChainBasicInfoInterface(Resource):
#     @basic_ns.doc(description=u"获得stellar主链基础信息\n可能的错误\n"
#                               u"119网络超时")
#     def get(self):
#         mainchainbasicnfo = self.getMainChainBasicInfo()
#         return create_response(XDCodeMsg.SUCCESS, data=mainchainbasicnfo)
#         # 获取主链基本信息
#
#     def getMainChainBasicInfo(self):
#         fail_data = None
#         # 从redis获取数据
#         try:
#             mainchainbasicnfo = eval(redisService.get('mainChainsInfos'))
#             print "redis获取"
#         except Exception as e:
#             mainchainbasicnfo = None
#             logging.error(e)
#         # 如果redis没有数据则从网页获取
#         if mainchainbasicnfo is None:
#             print "网页"
#             mainchainbasicnfo = getMainChainBasicInfos()
#             if isinstance(mainchainbasicnfo, XDCodeMsg):
#                 return mainchainbasicnfo, fail_data
#         return create_response(XDCodeMsg.SUCCESS, data=mainchainbasicnfo)
