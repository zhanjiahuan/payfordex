# coding:utf-8

from decimal import Decimal  # 十进制


def str_num_to_decimal(num):
    n = 0
    for i in num:
        if i == '.':
            n += 1
    if n > 1:
        return None
    if n > 0:
        float_len = num.split('.')[1]
        if len(float_len) > 7:
            return None
    if 'e' in num or 'E' in num:
        return None
    try:
        num = Decimal(num)
    except:
        return None
    else:
        return num

if __name__ == '__main__':
    amount = '0'
    amount = str_num_to_decimal(amount)
    if amount is None :
        print('无效参数')