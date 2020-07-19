# coding: utf-8
"""
结合掘金的数据使用 czsc 进行缠论技术分析

author: zengbin93
email: zeng_bin8888@163.com
date: 2020-02-02
========================================================================================================================
"""

from gm.api import *
from datetime import datetime
from czsc import KlineAnalyze, SolidAnalyze, Logger
import pandas as pd



# 在这里设置你的掘金token，用于获取数据
set_token("03210e0e39013a46836b3afb9d25b57b871df5a2")

log = Logger('all.log',level='debug').logger


def get_kline(symbol, end_date=None, freq='1d', k_count=3000):
    """从掘金获取历史K线数据

    参考： https://www.myquant.cn/docs/python/python_select_api#6fb030ec42984aff

    :param symbol:
    :param end_date: str
        交易日期，如 2019-12-31
    :param freq: str
        K线级别，如 1d
    :param k_count: int
    :return: pd.DataFrame
    """
    if not end_date:
        end_date = datetime.now()

    log.debug(symbol)
    log.debug(freq)
    log.debug(end_date)
    log.debug(k_count)

    df = history_n(symbol=symbol, frequency=freq, end_time=end_date,
                   fields='symbol,eob,open,close,high,low,volume',
                   count=k_count, df=True)
    if freq == '1d':
        df = df.iloc[:-1]
    df['dt'] = df['eob']
    df['vol'] = df['volume']
    df = df[['symbol', 'dt', 'open', 'close', 'high', 'low', 'vol']]
    df.sort_values('dt', inplace=True, ascending=True)
    df['dt'] = df.dt.apply(lambda x: x.strftime(r"%Y-%m-%d %H:%M:%S"))
    df.reset_index(drop=True, inplace=True)

    for col in ['open', 'close', 'high', 'low']:
        df[col] = df[col].apply(round, args=(2,))

    
    return df


def get_klines(symbol, end_date=None, freqs='60s,300s,1800s,1d', k_count=300):
    """获取不同级别K线"""
    freq_map = {"60s": "1分钟", "300s": "5分钟", "1800s": "30分钟", "1d": "日线"}
    klines = dict()
    freqs = freqs.split(",")
    for freq in freqs:
        df = get_kline(symbol, end_date, freq, k_count)
        klines[freq_map[freq]] = df
    return klines


def use_kline_analyze():
    print('=' * 100, '\n')
    print("KlineAnalyze 的使用方法：\n")
    kline = get_kline(symbol='SHSE.000001', end_date="2020-06-24")
    ka = KlineAnalyze(kline)
    print("线段：", ka.xd, "\n")
    print("中枢：", ka.zs, "\n")


def use_solid_analyze():
    print('=' * 100, '\n')
    print("SolidAnalyze 的使用方法：\n")
    klines = get_klines(symbol='SZSE.300455', end_date="2020-02-02")
    sa = SolidAnalyze(klines)

    # 查看指定级别的三买
    tb, _ = sa.is_third_buy('30分钟')
    print("指定级别三买：", tb, "\n")


if __name__ == '__main__':

    log.debug('start')
    pd.set_option('display.max_columns', 6000)    # 显示所有列
    pd.set_option('display.max_rows', 6000)      # 显示所有行
    pd.set_option('display.width', 6000)
    pd.set_option('display.max_colwidth',1000)
    

    use_kline_analyze()
    #use_solid_analyze()


