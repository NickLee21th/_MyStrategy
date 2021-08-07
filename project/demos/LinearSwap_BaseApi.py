#
#  火币 API
#  USDT 本位永续合约
#

from project.demos.Base_Api import *

HOST_PATH = "https://api.hbdm.vn"


#
# 【通用】获取合约指数信息， 该接口支持全仓模式和逐仓模式。
# GET /linear-swap-api/v1/swap_index
# 请求参数
# contract_code	| string| N | 指数代码 | 示例	"BTC-USDT","ETH-USDT"
# 返回参数
# status | string | Y |	请求处理结果 | 有效值 "ok"，"error"
# <data> | object array | Y | 数据集合
#   contract_code | string | 指数代码 | 示例 "BTC-USDT","ETH-USDT"...
#   index_price | decimal | 指数价格
#   index_ts | long | Y | 响应生成时间点，时间戳，单位：毫秒
# </data>
# ts | long | Y | 时间戳，单位：毫秒
#
# 【通用】获取合约指数信息， 该接口支持全仓模式和逐仓模式。
def Get_LinearSwapApi_v1_SwapIndex(contract_code="BTC-USDT"):
    return HbgAnyCall().callWebMethod(
        host_path=HOST_PATH,
        interface_path="/linear-swap-api/v1/swap_index",
        method_type="GET",
        headers=None,
        params={
            "contract_code": contract_code
        },
    )

#
# 【通用】获取市场最优挂单
# GET /linear-swap-ex/market/bbo
# 该接口支持全仓模式和逐仓模式
# 请求参数
# contract_code | string | Y | 合约代码，不填返回全部合约的最优挂单信息 | 示例 "BTC-USDT"
# 返回参数
# status | string | Y |	请求处理结果 | 有效值 "ok"，"error"
# <ticks> | object array | Y | 标记点集合
#   contract_code | string | Y | 合约代码 | 示例 "BTC-USDT","ETH-USDT"...
#   mrid | long | Y | 撮合ID，唯一标识
#   ask | array | Y | [卖1价,卖1量(张)]
#   bid | array | Y | [买1价,买1量(张)]
#   ts | long | Y | 系统检测 orderbook 时间点, 时间戳，单位：毫秒
# </ticks>
# ts | long | Y | 响应生成时间点，时间戳，单位：毫秒
#
# 【通用】获取市场最优挂单
def Get_LinearSwapEx_Market_Bbo(contract_code="BTC-USDT"):
    return HbgAnyCall().callWebMethod(
        host_path=HOST_PATH,
        interface_path="/linear-swap-ex/market/bbo",
        method_type="GET",
        headers=None,
        params={
            "contract_code": contract_code
        },
    )


#
# 【通用】获取K线数据，支持全仓模式和逐仓模式。
# GET /linear-swap-ex/market/history/kline
# 请求参数
# contract_code | string | Y | 合约代码 | 示例 "BTC-USDT"
# period | string | Y | K线类型 | 有效值 1min, 5min, 15min, 30min, 60min,4hour,1day,1week,1mon
# size | int | N | 获取数量 | 默认: 150 | 有效值 [1,2000]
# from | long | N | 开始时间戳 10位 单位S
# to | long | N | 结束时间戳 10位 单位S
# 请求参数备注
# 1、size与from&to 必填其一，若全不填则返回空数据。
# 2、如果填写from，也要填写to。最多可获取连续两年的数据。
# 3、如果size、from、to 均填写，会忽略from、to参数。
# 返回参数
# ch | string | Y | 数据所属的 channel，格式： market.period
# <data> | object array | Y | 数据集合
#   id | long | Y | K线ID,也就是K线时间戳，K线起始时间
#   vol | decimal | Y | 成交量(张)。 值是买卖双边之和
#   count | decimal | Y | 成交笔数。 值是买卖双边之和
#   open | decimal | Y | 开盘价
#   close | decimal | Y | 收盘价,当K线为最晚的一根时，是最新成交价
#   low	| decimal | Y | 最低价
#   high | decimal | Y | 最高价
#   amount | decimal | Y | 成交量(币), 即 (成交量(张) * 单张合约面值)。 值是买卖双边之和
#   trade_turnover | decimal | Y | 成交额，即 sum（每一笔成交张数 * 合约面值 * 成交价格）。 值是买卖双边之和
# </data>
# status | string | Y | 请求处理结果	"ok" , "error"
# ts | long | Y | 响应生成时间点，时间戳，单位：毫秒
#
# 【通用】获取K线数据，支持全仓模式和逐仓模式。
def Get_LinearSwapEx_Market_History_Kline(
        params=None,
):
    if params is None:
        params = {
            "contract_code": "BTC-USDT",
            "period": "5min",
            "size": 10,
        }
    return HbgAnyCall().callWebMethod(
        host_path=HOST_PATH,
        interface_path="/linear-swap-ex/market/history/kline",
        method_type="GET",
        headers=None,
        params=params
    )

#
# 【全仓】合约下单
# POST /linear-swap-api/v1/swap_cross_order
# 【请求参数】
# contract_code | string | Y | 合约代码 | 示例 "BTC-USDT"
# client_order_id | long | N | 客户自己填写和维护，必须为数字,请注意必须小于等于9223372036854775807
# price | decimal | N | 价格
# volume | long | Y | 委托数量(张)
# direction | string | Y | 仓位方向 | 有效值 "buy":买 "sell":卖
# offset | string | Y | 开平方向 | 有效值 "open":开 "close":平
# lever_rate | int | Y | 杠杆倍数, “开仓”若有10倍多单，就不能再下20倍多单;
#                        首次使用高倍杠杆(>20倍)，请使用主账号登录web端同意高倍杠杆协议后，才能使用接口下高倍杠杆(>20倍)
# order_price_type | string | Y | 订单报价类型
#                  | 有效值 "limit":限价  "opponent":对手价  "post_only":只做maker单，post only下单只受用户持仓数量限制
#                          "optimal_5":最优5档  "optimal_10":最优10档  "optimal_20":最优20档  "ioc":IOC订单  "fok":FOK订单
#                          "opponent_ioc":对手价-IOC下单  "optimal_5_ioc":最优5档-IOC下单
#                          "optimal_10_ioc":最优10档-IOC下单  "optimal_20_ioc":最优20档-IOC下单
#                          "opponent_fok":对手价-FOK下单  "optimal_5_fok":最优5档-FOK下单
#                          "optimal_10_fok":最优10档-FOK下单  "optimal_20_fok":最优20档-FOK下单
# tp_trigger_price | decimal | N | 止盈触发价格
# tp_order_price | decimal | N | 止盈委托价格（最优N档委托类型时无需填写价格）
# tp_order_price_type | string | N | 止盈委托类型
#                     | 默认:limit | 有效值  限价:limit  最优5档:optimal_5  最优10档:optimal_10  最优20档:optimal_20
# sl_trigger_price | decimal | N | 止损触发价格
# sl_order_price | decimal | N | 止损委托价格（最优N档委托类型时无需填写价格）
# sl_order_price_type | string | N | 止损委托类型
#                     | 默认:limit | 有效值  限价:limit  最优5档:optimal_5  最优10档:optimal_10  最优20档:optimal_20
# 【请求备注】
# 1. "limit":限价，"post_only":只做maker单，ioc:IOC订单，fok：FOK订单，这四种报价类型需要传价格，其他都不需要。
# 2. 若存在持仓，那么下单时杠杆倍数必须与持仓杠杆相同，否则下单失败。若需使用新杠杆下单，则必须先使用切换杠杆接口将持仓杠杆切换成功后再下单。
# 3. 只有开仓订单才支持设置止盈止损。
# 4. 止盈触发价格为设置止盈单必填字段，止损触发价格为设置止损单必填字段；若缺省触发价格字段则不会设置对应的止盈单或止损单。
# 【开平方向】
# 开多：买入开多(direction用buy、offset用open)
# 平多：卖出平多(direction用sell、offset用close)
# 开空：卖出开空(direction用sell、offset用open)
# 平空：买入平空(direction用buy、offset用close)
# 【返回参数】
# status | string | Y | 请求处理结果 | 有效值 "ok" , "error"
# <data> | object | Y | 数据列表
#   order_id | long | Y| 订单ID
#   order_id_str | string | Y| String类型订单ID
#   client_order_id | long | N| 用户下单时填写的客户端订单ID，没填则不返回
# </data>
# ts | long | Y | 响应生成时间点，时间戳，单位：毫秒
# 【返回备注】
# 1. order_id返回是18位，
# 2. nodejs和javascript默认解析18有问题，nodejs和javascript里面JSON.parse默认是int，超过18位的数字用json-bigint的包解析。
#
# 【全仓】合约下单
def Post_LinearSwapApi_v1_SwapCross_Order(
        access_key="", secret_key="",
        contract_code="BTC-USDT",  # 合约代码
        client_order_id=None,  # 客户维护的订单ID
        price=None,  # 价格
        volume=1,  # 委托数量(张)
        direction="buy",  # 仓位方向
        offset="open",  # 开平方向
        lever_rate=3,  # 杠杆倍数
        order_price_type="opponent",  # 订单报价类型
        tp_trigger_price=None,  # 止盈触发价格
        tp_order_price=None,  # 止盈委托价格
        tp_order_price_type=None,  # 止盈委托类型
        sl_trigger_price=None,  # 止损触发价格
        sl_order_price=None,  # 止损委托价格
        sl_order_price_type=None  # 止损委托类型
):
    params = {
        "contract_code": contract_code,  # 合约代码
        "volume": volume,  # 委托数量(张)
        "direction": direction,  # 仓位方向
        "offset": offset,  # 开平方向
        "lever_rate": lever_rate,  # 杠杆倍数
        "order_price_type": order_price_type  # 订单报价类型
    }
    if client_order_id is not None:  # 客户维护的订单ID
        params["client_order_id"] = client_order_id
    if price is not None:  # 价格
        params["price"] = price
    if tp_trigger_price is None:  # 止盈触发价格
        params["tp_trigger_price"] = tp_trigger_price
    if tp_order_price is None:  # 止盈委托价格
        params["tp_order_price"] = tp_order_price
    if tp_order_price_type is None:  # 止盈委托类型
        params["tp_order_price_type"] = tp_order_price_type
    if sl_trigger_price is None:  # 止损触发价格
        params["sl_trigger_price"] = sl_trigger_price
    if sl_order_price is None:  # 止损委托价格
        params["sl_order_price"] = sl_order_price
    if sl_order_price_type is None:  # 止损委托类型
        params["sl_order_price_type"] = sl_order_price_type
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path=HOST_PATH,
        interface_path="/linear-swap-api/v1/swap_cross_order",
        method_type="POST",
        headers=None,
        params=params
    )


#
# 【全仓】闪电平仓下单
# POST /linear-swap-api/v1/swap_cross_lightning_close_position
# 【请求参数】
# contract_code | true | string | 合约代码 | 示例 "BTC-USDT"
# volume | true | decimal | 委托数量（张）
# direction | true | string | 买卖方向 | 有效值  “buy”:买，“sell”:卖
# client_order_id | false | long |（API）客户自己填写和维护，必须保持唯一,请注意必须小于等于9223372036854775807
# order_price_type | false | string | 订单报价类型(平仓方式) | 不填，默认为“闪电平仓”
#                  | 有效值  "lightning"：闪电平仓，"lightning_ioc"：闪电平仓-IOC，"lightning_fok"：闪电平仓-FOK
# 【备注】
# 闪电平仓，是指在对手价平仓的基础上，实行'最优30档'成交，
#         即用户发出的平仓订单能够迅速以30档范围内对手方价格进行成交，未成交部分自动转为限价委托单。
# 【返回参数】
# status | true | string | 请求处理结果 | 有效值  "ok" :成功, "error"：失败
# ts | true | long | 响应生成时间点，单位：毫秒
# <data> | true | object | 字典
#   order_id | true | long | 订单ID[全局唯一]
#   order_id_str | true | string | String类型订单ID
#   client_order_id | false | int | 用户自己的订单id
# </data>
#
# 【全仓】闪电平仓下单
def Post_LinearSwapApi_v1_SwapCrossLightningClosePosition(
        access_key="", secret_key="",
        contract_code="BTC-USDT",  # 合约代码
        volume=1,  # 委托数量(张)
        direction="buy",  # 仓位方向
        client_order_id=None,  # 客户维护的订单ID
        order_price_type="opponent"  # 订单报价类型(平仓方式)
):
    params = {
        "contract_code": contract_code,  # 合约代码
        "volume": volume,  # 委托数量(张)
        "direction": direction  # 仓位方向
    }
    if client_order_id is not None:  # 客户维护的订单ID
        params["client_order_id"] = client_order_id
    if order_price_type is not None:  # 订单报价类型(平仓方式)
        params["order_price_type"] = order_price_type
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path=HOST_PATH,
        interface_path="/linear-swap-api/v1/swap_cross_lightning_close_position",
        method_type="POST",
        headers=None,
        params=params
    )


if __name__ == '__main__':
    ret = Post_LinearSwapApi_v1_SwapCross_Order(
        access_key="b4b263dd-5ac00f53-fr2wer5t6y-e399b",
        secret_key="4a67efff-6a19a91b-8d1a83e2-92c8f",
    )
    print_json(ret)
