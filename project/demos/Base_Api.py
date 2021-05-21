import datetime
from project.demos._hbg_anyCall import HbgAnyCall


# UNIX时间戳 转换为 datetime  显示
def TimeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d-%H-%M-%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)


# 返回历史K线数据。K线周期以新加坡时间为基准开始计算，例如日K线的起始周期为新加坡时间0时至新加坡时间次日0时。
# 当前 REST API 不支持自定义时间区间，如需要历史固定时间范围的数据，请参考 Websocket API 中的 K 线接口。
# 获取 hb10 净值时， symbol 请填写 “hb10”。
# 响应数据
# 字段名称	数据类型	描述
# id        long	调整为新加坡时间的时间戳，单位秒，并以此作为此K线柱的id
# amount	float	以基础币种计量的交易量
# count     integer	交易次数
# open      float	本阶段开盘价
# close     float	本阶段收盘价
# low       float	本阶段最低价
# high      float	本阶段最高价
# vo        float	以报价币种计量的交易量
def Get_kline_data(symbol="btcusdt", period="1min", size=3):
    return HbgAnyCall().callWebMethod(
        host_path="https://api.huobi.pro",
        interface_path="/market/history/kline",
        method_type="GET",
        headers=None,
        params={
            "symbol": symbol,  # btcusdt, ethbtc等
                               # （如需获取杠杆ETP净值K线，净值symbol = 杠杆ETP交易对symbol + 后缀‘nav’，
                               # 例如：btc3lusdtnav）
            "period": period,  # 1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1mon, 1week, 1year
            "size": size  # [1,2000]
        },
    )
