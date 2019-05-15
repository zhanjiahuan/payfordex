# # coding:utf-8
# import logging
#
# from stellar_base import horizon
#
# from app.utils.stellar import *
# from app.utils.session_pool import SessionPool
# from app.utils.utils import *
# from app.basic.xianda_basic_api import *
#
# session_pool = SessionPool().sessionPool
# submit_url_prefix = stellar_service()
#
#
# # 删除不需要的字段,也可自定义传入pop_list_key
# def pop_list(infos, pop_list_key=[]):
#     if not pop_list_key:
#         pop_list_key = [u'_links', u'envelope_xdr', u'result_xdr', u'result_meta_xdr',
#                         u'fee_meta_xdr',
#                         u'id', u'header_xdr']
#     for infokey in infos.keys():
#         if infokey in pop_list_key:
#             infos.pop(infokey)
#     return infos
#
#
# # 获取所有区块链信息
# def getLatestBlocksInfos(page_size, order, page_num):
#     url = submit_url_prefix + '/ledgers?cursor={}&limit={}&order={}'.format(page_num, page_size, order)
#     infos = session_pool.get(url).json()
#     if infos.get('status') is not None:
#         return XDCodeMsg.CodeMsg(123, 'page_num 或 order 无效')
#     block_infos = []
#     for info in infos['_embedded']['records']:
#         info['closed_at'] = utc_to_local(info['closed_at'])
#         block_infos.append(pop_list(info))
#     return block_infos
#
#
# def updateLatestLedgersToRedis():
#     blocks_infos = getLatestBlocksInfos(20, 'desc', 'now')
#     if isinstance(blocks_infos, XDCodeMsg):
#         logging.error('task func:updateLatestLedgersToRedis call getLatestBlocksInfo' + str(blocks_infos))
#         return
#     try:
#         redisService.set('ledgersInfo', str(blocks_infos))
#     except Exception as e:
#         logging.exception(e)
#
#
# # 获取最新的事物信息
# # def getLatestTransactionInfos(self, page_size, order, page_num):
# #     tran_infos = XiandaHorizon(horizon=self.getOneAvaStellarHorizonFromConsul()).transactions(
# #         params={'limit': page_size, 'order': order, 'cursor': page_num})
# #     if tran_infos.get('status') is not None:
# #         return XDCodeMsg.PAGENUM_OR_ORDER_NOT_VALID
# #     transaction_infos = []
# #     for info in tran_infos['_embedded']['records']:
# #         info['created_at'] = XiandaStellarUtil().utc_to_local(info['created_at'])
# #         transaction_infos.append(self.pop_list(info))
# #     return transaction_i
#
#
# # # 最新事物定时任务(最新的20条数据)
# # def updateLatestTransationsToRedis():
# #     tran_infos = getLatestTransactionInfos(20, 'desc', 'now')
# #     if isinstance(tran_infos, XDCodeMsg):
# #         logging.error('task func:updateLatestTransationsToRedis call getLatestTransationsInfo' + str(tran_infos))
# #         return
# #     try:
# #         redisService.set('transationsInfo', str(tran_infos))
# #     except Exception as e:
# #         logging.exception(e)
#
#
# #
# #
# # # 最新操作定时任务(最新的20条数据)
# # def updateLatestOpreationsToRedis():
# #     operation_infos = xiandaStellarBasicService.getLatestOperationsInfos(20, 'desc', 'now')
# #     if isinstance(operation_infos, XDCodeMsg.CM):
# #         logging.error('task func:updateLatestOpreationsToRedis call getLatestOpreation' + operation_infos.msg)
# #         return
# #     try:
# #         redisService.set('opreationsInfo', str(operation_infos))
# #     except Exception as e:
# #         logging.exception(e)
#
# # 获取主链基本信息
# def getMainChainBasicInfos():
#     horizonUrl = submit_url_prefix
#     port_info = horizon.query(horizonUrl)
#     url = submit_url_prefix + '/ledgers?cursor={}&limit={}&order={}'.format('now', 1, 'desc')
#     ledger_info = session_pool.get(url).json()
#     if port_info.get('status') is not None or ledger_info.get('status') is not None:
#         return XDCodeMsg.CodeMsg(124, '网络超时')
#     port_info.pop('network_passphrase')
#     port_info.pop('_links')
#     ledger_infos = ledger_info['_embedded']['records'][0]
#     ledger_infos.pop('header_xdr')
#     ledger_infos.pop('_links')
#     ledger_infos.pop('protocol_version')
#     ledger_infos['closed_at'] = utc_to_local(ledger_infos['closed_at'])
#     mainchainbasicnfo = dict(port_info, **ledger_infos)
#     return mainchainbasicnfo
#
#
# # 节点信息
# def updateLatestMainChainToRedis():
#     chain_infos = getMainChainBasicInfos()
#     if isinstance(chain_infos, XDCodeMsg):
#         logging.error('task func:updateLatestMainChainToRedis call getLatestMainChain' + str(chain_infos))
#         return
#     try:
#         redisService.set('mainChainsInfos', str(chain_infos))
#     except Exception as e:
#         logging.exception(e)
