# coding: utf-8

from stellar_base.keypair import Keypair

def pay_object(pay_secret_key):
    '''通过秘钥来获取公钥'''
    par_object = Keypair.from_seed(pay_secret_key)  # 实例化秘钥对象
    # address() 通过秘钥对象获取它的公钥 记获取出来的是bytes类型需要转码
    assert_issuer = par_object.address().decode()
    return assert_issuer

pay_secret_key = 'SDZPDZE4H5HCNR5RH2C6T32ZNORC6IQXLB6SQMJN6PVVSSMP5BCZIB2Z'

# print pay_object(pay_secret_key)
