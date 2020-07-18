# -*- coding:UTF-8 -*-

from gm.api import *
from datetime import datetime
from czsc import KlineAnalyze, SolidAnalyze, Logger
import pandas as pd
import configparser
import json
import os
import pandas as pd
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, parse_command_line, options
from tornado.web import RequestHandler, Application
from tornado.web import StaticFileHandler
from datetime import datetime, timedelta



log = Logger('all.log',level='debug').logger


def get_kline(symbol, end_date=None, freq='1d', k_count=30):
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

    log.debug(df)
    return df

def get_gm_kline(symbol, end_date, freq='D', k_count=3000):
    """从掘金获取历史K线数据"""

    if "-" not in end_date and isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y%m%d")
    freq_convert = {"60s": "1min", "300s": "5min", "1800s": "30min", "3600s": "60min", "1d": "D"}
    log.debug(freq_convert)
    freq_convert = {v: k for k, v in freq_convert.items()} #{'1min': '60s', '5min': '300s', '30min': '1800s', '60min': '3600s', 'D': '1d'}
    log.debug(freq_convert)
    if freq[-1] in ['n', 'D']:
        freq = freq_convert[freq]
        if freq.endswith('min'):
            end_date += timedelta(days=1)
    
    df = history_n(symbol=symbol, frequency=freq, end_time=end_date,
                   fields='symbol,eob,open,close,high,low,volume',
                   count=k_count, df=True)
    
    df['dt'] = df['eob']
    df['vol'] = df['volume']

    df = df[['symbol', 'dt', 'open', 'close', 'high', 'low', 'vol']] #调整列的顺序
    
    df.sort_values('dt', inplace=True, ascending=True)
    df['dt'] = df.dt.apply(lambda x: x.strftime(r"%Y-%m-%d %H:%M:%S"))
    df.reset_index(drop=True, inplace=True)
    for col in ['open', 'close', 'high', 'low']:
        df[col] = df[col].apply(round, args=(2,))  

    log.debug(df)  
    return df


class BaseHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")  # 这个地方可以写域名
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def post(self):
        self.write('some post')

    def get(self):
        self.write('some get')

    def options(self):
        self.set_status(204)
        self.finish()


class KlineHandler(BaseHandler):
    """k线"""
    def get(self):
        ts_code = self.get_argument('ts_code')
        freq = self.get_argument('freq')
        trade_date = self.get_argument('trade_date')
        if trade_date == 'null':
            trade_date = datetime.now().date().__str__().replace("-", "")
        log.debug(ts_code)
        log.debug(freq)
        log.debug(trade_date)
        kline = get_gm_kline(symbol=ts_code, end_date=trade_date, freq=freq, k_count=1440)
        ka = KlineAnalyze(kline)
        kline = pd.DataFrame(ka.kline)
        kline = kline.fillna("")
        columns = ["dt", "open", "close", "low", "high", "vol", 'fx_mark', 'fx', 'bi', 'xd']

        self.finish({'kdata': kline[columns].values.tolist()})        


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)    # 显示所有列
    pd.set_option('display.max_rows', None)      # 显示所有行
    log.debug("start")
    conf = configparser.ConfigParser()
    conf.readfp(open("config.ini"))
    token = conf.get("juejin","token")
    
    log.debug("set token")
    set_token(token)

    app = Application([
            ('/kline', KlineHandler),
    
        ],
        
        dubug=True
    )
    http_server = HTTPServer(app)
    http_server.listen(3000,'127.0.0.1')
    IOLoop.current().start()


