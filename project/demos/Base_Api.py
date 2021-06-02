import datetime
import math
# import json
import codecs
# import os
import yaml
from project.demos._hbg_anyCall import HbgAnyCall


# 读取 yaml 文件
def read_yaml(filename):
    fb = codecs.open(filename, "r", "utf-8")
    content = yaml.safe_load(fb)
    fb.close()
    return content


# 时间差转化为可读字符串
def Show_delta_time(delta_time):
    s_delta_time = ""
    if delta_time >= 24*60*60:
        days = math.trunc(delta_time/(24*60*60))
        left_delta_time = delta_time-days*24*60*60
        hours = math.trunc(left_delta_time/(60*60))
        left_delta_time = left_delta_time - hours*60*60
        minutes = math.trunc(left_delta_time/60)
        seconds = left_delta_time - minutes*60
        if days == 1:
            s_delta_time = "%s day" % days
        else:
            s_delta_time = "%s days" % days
        if hours == 1:
            s_delta_time += " %s hour" % hours
        else:
            s_delta_time += " %s hours" % hours
        if minutes == 1:
            s_delta_time += " %s minute" % minutes
        else:
            s_delta_time += " %s minutes" % minutes
        if seconds == 1:
            s_delta_time += " %s second" % seconds
        else:
            s_delta_time += " %s seconds" % seconds
    else:
        if delta_time >= 60*60:
            hours = math.trunc(delta_time/(60*60))
            left_delta_time = delta_time - hours*60*60
            minutes = math.trunc(left_delta_time/60)
            seconds = left_delta_time - minutes*60
            if hours == 1:
                s_delta_time += " %s hour" % hours
            else:
                s_delta_time += " %s hours" % hours
            if minutes == 1:
                s_delta_time += " %s minute" % minutes
            else:
                s_delta_time += " %s minutes" % minutes
            if seconds == 1:
                s_delta_time += " %s second" % seconds
            else:
                s_delta_time += " %s seconds" % seconds
        else:
            if delta_time >= 60:
                minutes = math.trunc(delta_time / 60)
                seconds = delta_time - minutes * 60
                if minutes == 1:
                    s_delta_time += " %s minute" % minutes
                else:
                    s_delta_time += " %s minutes" % minutes
                if seconds == 1:
                    s_delta_time += " %s second" % seconds
                else:
                    s_delta_time += " %s seconds" % seconds
            else:
                seconds = delta_time
                if seconds == 1:
                    s_delta_time += " %s second" % seconds
                else:
                    s_delta_time += " %s seconds" % seconds
    return s_delta_time


# UNIX时间戳 转换为 datetime  显示
def TimeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d-%H-%M-%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)

# 限价买入/卖出时，买入量/卖出量 Base 的小数位精度。
def get_amount_precision(symbol=""):
    amount_precision = 4
    if symbol == "ethusdt":
        amount_precision = 4
    elif symbol == "btcusdt":
        amount_precision = 6
    return amount_precision

# 限价买入/卖出时，买入价/卖出价 Quoter 的小数位精度。
def get_price_precision(symbol=""):
    price_precision = 2
    if symbol == "ethusdt":
        price_precision = 2
    elif symbol == "btcusdt":
        price_precision = 2
    return price_precision



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


# 下单 - 发送一个新订单到火币以进行撮合
# 响应数据
# 返回的主数据对象是一个对应下单单号的字符串。
# 如client order ID（在24小时内）被复用，节点将返回错误消息invalid.client.order.id。
def Post_order_place(
        access_key, secret_key,
        account_id, symbol, type_value, amount,
        price=None, source=None, client_order_id=None,
        stop_price=None, operator=None
):
    params = {
        "account-id": account_id,  # 账户 ID，取值参考 GET /v1/account/accounts。
                                   # 现货交易使用 ‘spot’ 账户的 account-id；
                                   # 逐仓杠杆交易，请使用 ‘margin’ 账户的 account-id；
                                   # 全仓杠杆交易，请使用 ‘super-margin’ 账户的 account-id
                                   # 交易对,即btcusdt, ethbtc...（取值参考GET /v1/common/symbols）
        "symbol": symbol,  # 交易对,即btcusdt, ethbtc...（取值参考GET /v1/common/symbols）
        "type": type_value,  # 订单类型，包括 buy-market, sell-market, buy-limit, sell-limit,
                             # buy-ioc, sell-ioc, buy-limit-maker, sell-limit-maker,
                             # buy-stop-limit, sell-stop-limit, buy-limit-fok, sell-limit-fok,
                             # buy-stop-limit-fok, sell-stop-limit-fok
        "amount": amount  # 订单交易量（市价买单为订单交易额）
    }
    if price is not None:
        params["price"] = price   # 订单价格（对市价单无效）
    if source is not None:
        params["source"] = source  # 现货交易填写“spot-api”(默认值)，
                                   # 逐仓杠杆交易填写“margin-api”，
                                   # 全仓杠杆交易填写“super-margin-api”,
                                   # C2C杠杆交易填写"c2c-margin-api"
    if client_order_id is not None:
        params["client-order-id"] = client_order_id   # 用户自编订单号（最大长度64个字符，须在24小时内保持唯一性）
    if stop_price is not None:
        params["stop-price"] = stop_price   # 止盈止损订单触发价格
    if operator is not None:
        params["operator"] = operator  # 止盈止损订单触发价运算符
                                       # gte – greater than and equal (>=),
                                       # lte – less than and equal (<=)
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path="https://api.huobi.pro",
        interface_path="/v1/order/orders/place",
        method_type="POST",
        headers=None,
        params=params
    )


# 返回指定交易对市场深度数据
def Get_market_depth(
        host_path="https://api.huobi.pro",
        symbol="btcusdt",
        depth=5,  # 返回深度的数量, 取值范围 5，10，20
        type_value="step0"  # 深度的价格聚合度
):
    params = {
        "symbol": symbol,
        "depth": depth,  # 返回深度的数量, 取值范围 5，10，20
        "type": type_value  # 深度的价格聚合度
    }
    anyCall = HbgAnyCall()
    ret = anyCall.callWebMethod(
        host_path=host_path,
        interface_path="/market/depth",
        method_type="GET",
        headers=None,
        params=params
    )
    # anyCall.print_json(ret)
    return ret


# 查询订单详情
# API Key 权限：读取
# 限频值（NEW）：50次/2s
#
# 此接口返回指定订单的最新状态和详情。通过API创建的订单，撤销超过2小时后无法查询。通过API创建的订单返回order-id，
# 按此order-id查询订单还是返回base-record-invalid是因为系统内部处理有延迟，但是不影响成交。
# 建议您后续重试查询或者通过订阅订单推送WebSocket消息查询。
#
# HTTP 请求
# GET /v1/order/orders/{order-id}
# 请求参数
# 参数名称	是否必须	类型	描述	默认值	取值范围
# order-id	true	string	订单ID，填在path中
# Response:
# {
#   "data":
#   {
#     "id": 59378,
#     "symbol": "ethusdt",
#     "account-id": 100009,
#     "amount": "10.1000000000",
#     "price": "100.1000000000",
#     "created-at": 1494901162595,
#     "type": "buy-limit",
#     "field-amount": "10.1000000000",
#     "field-cash-amount": "1011.0100000000",
#     "field-fees": "0.0202000000",
#     "finished-at": 1494901400468,
#     "user-id": 1000,
#     "source": "api",
#     "state": "filled",
#     "canceled-at": 0
#   }
# }
# 响应数据
# 字段名称	是否必须	数据类型	描述	取值范围
# account-id	true	long	账户 ID
# amount	true	string	订单数量
# canceled-at	false	long	订单撤销时间
# created-at	true	long	订单创建时间
# field-amount	true	string	已成交数量
# field-cash-amount	true	string	已成交总金额
# field-fees	true	string	已成交手续费（准确数值请参考matchresults接口）
# finished-at	false	long	订单变为终结态的时间，不是成交时间，包含“已撤单”状态
# id	true	long	订单ID
# client-order-id	false	string	用户自编订单号（所有open订单可返回client-order-id（如有）；
# 仅7天内（基于订单创建时间）的closed订单（state <> canceled）可返回client-order-id（如有）；
# 仅24小时内（基于订单创建时间）的closed订单（state = canceled）可返回client-order-id（如有））
# price	true	string	订单价格
# source	true	string	订单来源	api
# state	true	string	订单状态	所有可能的订单状态（见本章节简介）
# symbol	true	string	交易对	btcusdt, ethbtc, rcneth ...
# type	true	string	订单类型	所有可能的订单类型（见本章节简介）
# stop-price	false	string	止盈止损订单触发价格
# operator	false	string	止盈止损订单触发价运算符	gte,lte
def Get_v1_order_orders_orderId(
        access_key, secret_key,
        host_path="https://api.huobi.pro",
        order_id="",
):
    interface_path = "/v1/order/orders/%s" % order_id
    anyCall = HbgAnyCall()
    ret = anyCall.callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path=host_path,
        interface_path=interface_path,
        method_type="GET",
        headers=None,
        params=None
    )
    anyCall.print_json(ret)
    return ret


# 订单状态 (state):
#
# created：已创建，该状态订单尚未进入撮合队列。
# submitted : 已挂单等待成交，该状态订单已进入撮合队列当中。
# partial-filled : 部分成交，该状态订单在撮合队列当中，订单的部分数量已经被市场成交，等待剩余部分成交。
# filled : 已成交。该状态订单不在撮合队列中，订单的全部数量已经被市场成交。
# partial-canceled : 部分成交撤销。该状态订单不在撮合队列中，此状态由partial-filled转化而来，订单数量有部分被成交，但是被撤销。
# canceling : 撤销中。该状态订单正在被撤销的过程中，因订单最终需在撮合队列中剔除才会被真正撤销，所以此状态为中间过渡态。
# canceled : 已撤销。该状态订单不在撮合订单中，此状态订单没有任何成交数量，且被成功撤销。


# 撤销订单
# 此接口发送一个撤销订单的请求。
#
# 此接口只提交取消请求，实际取消结果需要通过订单状态，撮合状态等接口来确认。
# HTTP 请求
# POST /v1/order/orders/{order-id}/submitcancel
# 请求参数
# 参数名称	是否必须	类型	描述	默认值	取值范围
# order-id	true	string	订单ID，填在path中
# 响应数据
# 返回的主数据对象是一个对应下单单号的字符串。
# 错误码
# 返回字段列表中，order-state的可能取值包括 -
# order-state	Description
# -1 order was already closed in the long past (order state = canceled, partial-canceled, filled, partial-filled)
# 5	 partial-canceled
# 6	 filled
# 7	 canceled
# 10 cancelling
def Post_v1_order_orders_orderId_submitcancel(
        access_key, secret_key,
        host_path="https://api.huobi.pro",
        order_id="",
):
    interface_path = "/v1/order/orders/%s/submitcancel" % order_id
    anyCall = HbgAnyCall()
    ret = anyCall.callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path=host_path,
        interface_path=interface_path,
        method_type="POST",
        headers=None,
        params=None
    )
    anyCall.print_json(ret)
    return ret