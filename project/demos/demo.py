import datetime
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
import logging
import time


class DemoStrategy:
    BASE_INVEST = 20
    current_balance = BASE_INVEST
    once_invest = BASE_INVEST / 2
    last_symbol = ""
    last_currency = ""
    last_amount = 0.0
    earning_ratio = 0.0
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    etp = ""
    dt_stamp = ""
    demo_logger = None
    data_dict = {}

    def get_from_data_dict(self, index_i):
        OK = False
        earn_value_A = ""
        earn_value_B = ""
        if index_i in self.data_dict.keys():
            earn_value_A = self.data_dict[index_i]["earn_value_A"]
            earn_value_B = self.data_dict[index_i]["earn_value_B"]
            OK = True
        return OK, earn_value_A, earn_value_B

    def logger_init(self,
                    log_file_template="demo_log/demo_%s_%s.log"
                    ):
        logger = logging.getLogger(self.etp)
        logger.setLevel(level=logging.INFO)
        dt_value = self.dt_stamp
        handler = logging.FileHandler(log_file_template % (self.etp, dt_value))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.demo_logger = logger

    def demo_print(self, log, ignore=False, end=None):
        if ignore:
            log = None
        if log is not None:
            self.demo_logger.info(str(log))
            if end is not None:
                print(str(log), end=end)
            else:
                print(str(log))

    # 市价买入指定币种
    def buy_market(self, symbol=""):
        if symbol == "":
            return False
        ret = False
        retry_count = 0
        response = None
        while ret is False and retry_count < 10:
            response = Post_order_place(
                access_key=self.access_key,
                secret_key=self.secret_key,
                account_id=self.account_id,
                symbol=symbol,
                type_value="buy-market",
                amount=10,
            )
            if response is not None:
                status = response["status"]
                if status == "ok":
                    ret = True
                else:
                    ret = False
                    retry_count += 1
                    time.sleep(2)
                    continue
            else:
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return response

    # 市价卖出指定币种
    def sell_market(self, symbol="", amount=0):
        if symbol == "" or amount <= 0:
            return False
        ret = False
        retry_count = 0
        response = None
        while ret is False and retry_count < 10:
            response = Post_order_place(
                access_key=self.access_key,
                secret_key=self.secret_key,
                account_id=self.account_id,
                symbol=symbol,
                type_value="sell-market",
                amount=amount,
            )
            if response is not None:
                status = response["status"]
                if status == "ok":
                    ret = True
                else:
                    ret = False
                    retry_count += 1
                    time.sleep(2)
                    continue
            else:
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return response

    # 行动器

    # 行动
    def demon_action(self):
        self.logger_init(log_file_template="demo_action_log/action_%s_%s.txt")
        self.demo_print("I'm %s in demo_action" % self.etp)
        count = 0
        while count < 1000:
            time_stamp = int(time.time())
            self.do_action()
            time_stamp_end = int(time.time())
            sleep_time = 60 * 5 - (time_stamp_end - time_stamp)
            print("sleep %s seconds ....." % sleep_time)
            time.sleep(sleep_time)
            count += 1

    # 行动器
    def do_action(self):
        try:
            period = "5min"  # 1min, 5min, 15min, 30min
            size = 2000
            step_range = int(size / 2)
            cur_ts = 1000
            last_ts = 0
            trend_base_list = None
            trend_3l_list = None
            trend_3s_list = None
            while (cur_ts-last_ts) > (60*5):
                trend_base_list, trend_3l_list, trend_3s_list \
                    = self.get_ALL_symbol_trend_data(
                    symbol_base=(self.etp + "usdt"),
                    symbol_l=(self.etp + "3lusdt"),
                    symbol_s=(self.etp + "3susdt"),
                    period=period,  # 1min, 5min, 15min, 30min
                    size=size,
                )
                last_ts = trend_base_list[0]["dt"]
                self.demo_print("last_ts = %s  %s " % (last_ts, timeStamp_to_datetime(last_ts)))
                cur_ts = int(time.time())
                self.demo_print("cur_ts = %s  %s " % (cur_ts, timeStamp_to_datetime(cur_ts)))
            print("OK -step 1")
            last_ts, last_trend, invest_direction = self.judge_invest_direction(
                trend_base_list=trend_base_list,
                trend_3l_list=trend_3l_list,
                trend_3s_list=trend_3s_list,
                symbol_base=(self.etp + "usdt"),
                start_point=step_range-1,
                end_point=-1,
            )
            self.demo_print("last_ts = %s  %s " % (last_ts, timeStamp_to_datetime(last_ts)))
            cur_ts = int(time.time())
            self.demo_print("cur_ts = %s  %s " % (cur_ts, timeStamp_to_datetime(cur_ts)))
            self.demo_print("(cur_ts-last_ts) = %s" % (cur_ts-last_ts))
            assert (60*5) < (cur_ts-last_ts)
            new_cur_ts = int(time.time())
            self.demo_print("new_cur_ts = %s  %s " % (new_cur_ts, timeStamp_to_datetime(new_cur_ts)))
            # 获取交易对价格
            symbol = ""
            currency = ""
            if last_trend == 1:
                self.demo_print("last_trend = 涨")
                symbol = self.etp + "3lusdt"
                currency = self.etp + "3l"
            elif last_trend == -1:
                self.demo_print("last_trend = 跌")
                symbol = self.etp + "3susdt"
                currency = self.etp + "3s"
            else:
                self.demo_print("last_trend = 平")
            self.demo_print("invest_direction = %s" % invest_direction)
            cur_price = "0.0"
            ts = 1
            if symbol != "":
                ts, cur_price = get_current_price(
                    symbol=symbol,
                )
                ts = int(ts/1000)
                self.demo_print("symbol = %s,  cur_price = %s" % (symbol, cur_price))
                self.demo_print("ts = %s  %s " % (ts, timeStamp_to_datetime(ts)))
                if self.last_symbol == "":
                    self.demo_print("current_balance = %s  %s"
                               % (self.current_balance, timeStamp_to_datetime(ts)))
                    self.last_symbol = symbol
                    self.last_currency = currency
                    self.last_amount = self.once_invest / cur_price
                    self.current_balance -= self.once_invest
                else:
                    sell_ts, sell_cur_price = get_current_price(
                        symbol=self.last_symbol,
                    )
                    sell_ts = int(sell_ts/1000)
                    self.current_balance += sell_cur_price * self.last_amount
                    self.demo_print("current_balance = %s  %s"
                               % (self.current_balance, timeStamp_to_datetime(sell_ts)))
                    self.earning_ratio = (self.current_balance-self.BASE_INVEST) / self.BASE_INVEST
                    self.demo_print("收益率 = %s" % self.earning_ratio)
                    self.last_symbol = symbol
                    self.last_currency = currency
                    self.last_amount = self.once_invest / cur_price
                    self.current_balance -= self.once_invest
            self.demo_print("=========================================")
        except Exception as ex:
            self.demo_print("Exception in demon_action")
            self.demo_print("ex = %s" % ex)

    # 预言机
    def demon_prediction(self):
        self.logger_init()
        self.demo_print("I'm %s" % self.etp)
        try:
            period = "5min"  # 1min, 5min, 15min, 30min
            size = 2000
            step_range = int(size / 4)
            trend_base_list, trend_3l_list, trend_3s_list \
                = self.get_ALL_symbol_trend_data(
                symbol_base=(self.etp + "usdt"),
                symbol_l=(self.etp + "3lusdt"),
                symbol_s=(self.etp + "3susdt"),
                period=period,  # 1min, 5min, 15min, 30min
                size=size,
            )
            print("OK -step 1")
            invest_direction_list = []
            for i in range(int(size / 2) - 1, -1, -1):
                print("%s -step 1-%s" % (self.etp, i))
                _, _, invest_direction = self.judge_invest_direction(
                    trend_base_list=trend_base_list,
                    trend_3l_list=trend_3l_list,
                    trend_3s_list=trend_3s_list,
                    symbol_base=(self.etp + "usdt"),
                    start_point=i + step_range,
                    end_point=i,
                )
                # demo_print("invest_direction = %s" % invest_direction)
                invest_direction_list.append(invest_direction)
            # demo_print(invest_direction_list)
            self.demo_print("\n")
            self.show_invest_direction(invest_direction_list)
            # demo_print("OK -step 2")
            earn_value = self.deduce_earn(
                symbol_base=(self.etp + "usdt"),
                invest_direction_list=invest_direction_list,
                start_point=int(size / 2) - 1,
                end_point=0,
                trend_base_list=trend_base_list,
                trend_3l_list=trend_3l_list,
                trend_3s_list=trend_3s_list,
            )
            self.demo_print("=========================================")
        except Exception as ex:
            self.demo_print("Exception in demon_prediction")
            self.demo_print("ex = %s" % ex)

    def deduce_earn(
            self,
            symbol_base,
            invest_direction_list, start_point, end_point,
            trend_base_list, trend_3l_list, trend_3s_list
    ):
        # start = start_point
        # end = end_point - 1
        # earn = 0
        pre_trend = ""
        earn_value = 0.0
        no_change_count = 0
        try:
            for i in range(start_point, end_point - 1, -1):
                # demo_print("%s %s" % (start_point-i, invest_direction_list[start_point-i]))
                if invest_direction_list[start_point - i] == "no_plan":
                    pre_trend = trend_base_list[i]["trend"]
                    continue
                if trend_base_list[i]["trend"] == 0:  # 平
                    no_change_count = no_change_count + 1
                    continue
                if pre_trend == "":
                    pre_trend = trend_base_list[i]["trend"]
                    continue
                if invest_direction_list[start_point - i] == "planA":
                    earn = -1.0
                    if pre_trend == trend_base_list[i]["trend"]:
                        earn = 1.0
                    if pre_trend == -1:  # 跌
                        earn_value = earn_value + abs(trend_3s_list[i]["change_rate"]) * earn
                    elif pre_trend == 1:  # 涨
                        earn_value = earn_value + abs(trend_3l_list[i]["change_rate"]) * earn
                elif invest_direction_list[start_point - i] == "planB":
                    earn = 1.0
                    if pre_trend == trend_base_list[i]["trend"]:
                        earn = -1.0
                    if pre_trend == -1:  # 跌
                        earn_value = earn_value + abs(trend_3l_list[i]["change_rate"]) * earn
                    elif pre_trend == 1:  # 涨
                        earn_value = earn_value + abs(trend_3s_list[i]["change_rate"]) * earn
                pre_trend = trend_base_list[i]["trend"]
        except Exception as ex:
            self.demo_print("Exception in deduce_earn")
            self.demo_print(ex)
        self.demo_print("%s .... earn_value = %s" % (symbol_base, earn_value))
        self.demo_print("%s .... no_change_count = %s" % (symbol_base, no_change_count))
        return earn_value

    def show_invest_direction(self, invest_direction_list):
        invest_direction = ""
        count_num = 0
        for item in invest_direction_list:
            if item == invest_direction:
                count_num += 1
            else:
                if invest_direction != "":
                    self.demo_print("%s: %s" % (invest_direction, count_num))
                    count_num = 1
                    invest_direction = item
                else:
                    invest_direction = item
                    count_num += 1
        self.demo_print("%s: %s" % (invest_direction, count_num))
        return True

    # 获取基础币种，3倍多，3倍空的历史数据
    def get_ALL_symbol_trend_data(self,
            symbol_base="btcusdt",
            symbol_l="btc3lusdt",
            symbol_s="btc3susdt",
            period="1min",
            size=2000,
    ):
        hbgAnyCall = HbgAnyCall()
        # base
        symbol = symbol_base
        trend_base_list = self.get_symbol_trend_data(
            symbol=symbol,
            period=period, size=size
        )
        assert trend_base_list
        # 3l
        symbol = symbol_l
        trend_3l_list = self.get_symbol_trend_data(
            symbol=symbol,
            period=period, size=size
        )
        assert trend_3l_list
        # 3s
        symbol = symbol_s
        trend_3s_list = self.get_symbol_trend_data(
            symbol=symbol,
            period=period, size=size
        )
        assert trend_3s_list
        return trend_base_list, trend_3l_list, trend_3s_list

    # 获取交易对的K线信息，整理后返回。
    def get_symbol_trend_data(self, symbol, period, size):
        trend_symbol_list = []
        try:
            k_line_res = None
            ret = False
            retry_count = 0
            while ret is False and retry_count < 10:
                k_line_res = Get_kline_data(
                    symbol=symbol,
                    period=period, size=size
                )
                if k_line_res is None or k_line_res["status"] != "ok":
                    ret = False
                    retry_count += 1
                    time.sleep(2)
                    continue
                else:
                    break
            if k_line_res is not None and k_line_res["status"] == "ok":
                res_data = k_line_res["data"]
                for item in res_data:
                    last_ts = item["id"]
                    cur_ts = int(time.time())
                    delta = cur_ts-last_ts
                    finished = True
                    if delta < (60*5):
                        finished = False
                    trend_symbol_item = {
                        "dt": item["id"],
                        "symbol": symbol,
                        "open": item["open"],
                        "close": item["close"],
                        "finished": finished
                    }
                    trend = 0  # 平
                    change_rate = (item["close"] - item["open"]) / item["open"]
                    if change_rate < 0:  # -0.0001:
                        trend = -1  # 跌
                    elif change_rate > 0:  # 0.0001:
                        trend = 1  # 涨
                    trend_symbol_item["change_rate"] = change_rate
                    trend_symbol_item["trend"] = trend
                    trend_symbol_list.append(trend_symbol_item)
                return trend_symbol_list
            else:
                self.demo_print("Failed in get_symbol_trend_data! ")
                self.demo_print("symbol=%s period=%s size=%s" % (symbol, period, size))
                return False
        except Exception as ex:
            self.demo_print("Exception in get_symbol_trend_data!")
            self.demo_print(ex)
            return False

    # 依据历史趋势判定下一步的投资计划
    def judge_invest_direction(
            self,
            trend_base_list,
            trend_3l_list,
            trend_3s_list,
            symbol_base="btc",
            start_point=1500,
            end_point=1000,
    ):
        (
            count_A_earn, count_B_earn,
            A_greater_than_B, A_greater_than_B_sum_value,
            B_greater_than_A, B_greater_than_A_sum_value
        ) = \
            self.calculate_trend_data(
                trend_base_list=trend_base_list,
                trend_3l_list=trend_3l_list,
                trend_3s_list=trend_3s_list,
                symbol_base=symbol_base,
                start_point=start_point,
                end_point=end_point,
        )
        step_range = int(start_point) - int(end_point)
        if trend_base_list[0]["finished"]:
            index = 0
        else:
            index = 1
            assert trend_base_list[1]["finished"]
        last_trend = trend_base_list[index]["trend"]
        last_ts = trend_base_list[index]["dt"]
        invest_direction = "no_plan"
        if count_B_earn > 0 and count_B_earn > count_A_earn and count_B_earn > (step_range * 0.8):
            invest_direction = "planB"
        elif count_A_earn > 0 and count_A_earn > count_B_earn and count_A_earn > (step_range * 0.8):
            invest_direction = "planA"
        return last_ts, last_trend, invest_direction

    # 计算指定时长内的趋势数据
    def calculate_trend_data(
            self,
            trend_base_list,
            trend_3l_list,
            trend_3s_list,
            symbol_base="btc",
            start_point=1500,
            end_point=1000,
    ):
        try:
            count_A_earn = 0
            count_B_earn = 0
            A_greater_than_B = 0
            B_greater_than_A = 0
            A_greater_than_B_sum_value = 0
            B_greater_than_A_sum_value = 0
            step_range = start_point - end_point
            for index_i in range(start_point, end_point, -1):
                OK, earn_value_A, earn_value_B \
                    = self.get_from_data_dict(index_i)
                if not OK:
                    earn_value_A \
                        = plan_A(symbol_base, index_i + step_range, index_i,
                                 trend_base_list, trend_3l_list, trend_3s_list)
                    earn_value_B \
                        = plan_B(symbol_base, index_i + step_range, index_i,
                                 trend_base_list, trend_3l_list, trend_3s_list)
                    self.data_dict[index_i] = {
                        "earn_value_A": earn_value_A,
                        "earn_value_B": earn_value_B
                    }
                if earn_value_A > 0:
                    count_A_earn += 1
                if earn_value_B > 0:
                    count_B_earn += 1
                if earn_value_A > 0 and earn_value_A > earn_value_B:
                    A_greater_than_B += 1
                    A_greater_than_B_sum_value += (earn_value_A - earn_value_B)
                if earn_value_B > 0 and earn_value_B > earn_value_A:
                    B_greater_than_A += 1
                    B_greater_than_A_sum_value += (earn_value_B - earn_value_A)
            ignore = True
            hbgAnyCall.log_print("\nsymbol_base = %s" % symbol_base, ignore=ignore)
            hbgAnyCall.log_print("step_range = %s" % step_range, ignore=ignore)
            hbgAnyCall.log_print("count_A_earn = %s" % count_A_earn, ignore=ignore)
            hbgAnyCall.log_print("count_B_earn = %s" % count_B_earn, ignore=ignore)
            hbgAnyCall.log_print("%s: A_greater_than_B = %s" % (symbol_base, A_greater_than_B), ignore=ignore)
            hbgAnyCall.log_print("%s: A_greater_than_B_sum_value = %s" % (symbol_base, A_greater_than_B_sum_value),
                                 ignore=ignore)
            hbgAnyCall.log_print("%s: B_greater_than_A = %s" % (symbol_base, B_greater_than_A), ignore=ignore)
            hbgAnyCall.log_print("%s: B_greater_than_A_sum_value = %s" % (symbol_base, B_greater_than_A_sum_value),
                                 ignore=ignore)
            return count_A_earn, count_B_earn, \
                   A_greater_than_B, A_greater_than_B_sum_value, \
                   B_greater_than_A, B_greater_than_A_sum_value
        except Exception as ex:
            self.demo_print("Exception in calculate_trend_data")
            self.demo_print(ex)
            return False


hbgAnyCall = HbgAnyCall()

logger = logging.getLogger("demo")
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler("demo.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def demo_print(log, ignore=False, end=None):
    if ignore:
        log = None
    if log is not None:
        logger.info(str(log))
        if end is not None:
            print(str(log), end=end)
        else:
            print(str(log))

def API_v2_account_repayment(access_key, secret_key,):
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path="https://api.huobi.pro",
        interface_path="/v2/account/repayment",
        method_type="POST",
        headers=None,
        params={
            "accountId": "19084939",  # 全仓  # "19085211" # 逐仓 (btcusdt),
            "currency": "usdt",
            "amount": "100",
        },
    )


# 返回当前交易对的最新的交易价格
def get_current_price(symbol="btcusdt"):
    current_price = 0.0
    ts = 0
    ret = False
    retry_count = 0
    while ret is False and retry_count < 10:
        response = Get_market_trade(
            symbol=symbol,
        )
        if response is not None:
            status = response["status"]
            ts = response["ts"]
            if status == "ok":
                tick = response["tick"]
                data = tick["data"]
                ret = True
                bFind = False
                for data_item in data:
                    current_price = data_item["price"]
                    bFind = True
                    break
                if not bFind:
                    print("Failed to get current price, symbol=%s" % symbol)
            else:
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        else:
            ret = False
            retry_count += 1
            time.sleep(2)
            continue
    return ts, current_price


# 返回指定交易对最新的一个交易记录。
def Get_market_trade(symbol="btcusdt"):
    params = {
        "symbol": symbol,
    }
    return HbgAnyCall().callWebMethod(
        host_path="https://api.huobi.pro",
        interface_path="/market/trade",
        method_type="GET",
        headers=None,
        params=params
    )

# 返回历史K线数据。K线周期以新加坡时间为基准开始计算，例如日K线的起始周期为新加坡时间0时至新加坡时间次日0时。
# 当前 REST API 不支持自定义时间区间，如需要历史固定时间范围的数据，请参考 Websocket API 中的 K 线接口。
# 获取 hb10 净值时， symbol 请填写 “hb10”。
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


#  账户余额 - 查询指定账户的余额，支持以下账户：
#  spot：现货账户， margin：逐仓杠杆账户，otc：OTC 账户，
#  point：点卡账户，super-margin：全仓杠杆账户,
#  investment: C2C杠杆借出账户, borrow: C2C杠杆借入账户
def Get_accounts_balance(
        access_key, secret_key,
        account_id
):
    params = {
        "account-id": account_id,  # 填在 path 中，取值参考 GET /v1/account/accounts
    }
    interface_path = "/v1/account/accounts/%s/balance" % account_id
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path="https://api.huobi.pro",
        interface_path=interface_path,
        method_type="GET",
        headers=None,
        params=params
    )


# 获取指定币种的当前可用余额
def get_currency_balance(
        access_key, secret_key,
        account_id,
        currency,   # 币种名称
        type_value  # trade: 交易余额，frozen: 冻结余额, loan: 待还借贷本金,
                    # interest: 待还借贷利息, lock: 锁仓, bank: 储蓄
):
    balance_value = "-1"
    ret = False
    retry_count = 0
    while ret is False and retry_count < 10:
        response = Get_accounts_balance(
            access_key=access_key, secret_key=secret_key,
            account_id=account_id
        )
        if response is not None:
            status = response["status"]
            if status == "ok":
                data = response["data"]
                balance_list = data["list"]
                ret = True
                bFind = False
                for balance_item in balance_list:
                    if balance_item["currency"] == currency and balance_item["type"] == type_value:
                        balance_value = balance_item["balance"]
                        bFind = True
                        break
                if not bFind:
                    print("Failed to get the balance, currency=%s, type_value=%s" % (currency, type_value))
            else:
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        else:
            ret = False
            retry_count += 1
            time.sleep(2)
            continue
    return balance_value


# 返回指定订单的成交明细
def Get_orders_matchresults(
        access_key, secret_key,
        order_id,  # 订单ID，填在path中
):
    params = {
        "order-id": order_id,  # 填在 path 中，取值参考 GET /v1/account/accounts
    }
    interface_path = "/v1/order/orders/%s/matchresults" % order_id
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path="https://api.huobi.pro",
        interface_path=interface_path,
        method_type="GET",
        headers=None,
        params=params
    )


# 获取ETP的持仓限额
def Get_etp_limit(
        access_key, secret_key,
        currency,  # 币种,支持批量查询，单次最多可查10个币种
):
    params = {
        "currency": currency,  # 币种,支持批量查询，单次最多可查10个币种
    }
    interface_path = "/v2/etp/limit"
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path="https://api.huobi.pro",
        interface_path=interface_path,
        method_type="GET",
        headers=None,
        params=params
    )


# UNIX时间戳 转换为 datetime  显示
def timeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d %H:%M:%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)


# 基于K线的计算
def calculate_base_on_KLine(
        symbol_base="btcusdt",
        symbol_l="btc3lusdt",
        symbol_s="btc3susdt",
        period="1min",
        size=2000,
    ):
    trend_base_list, trend_3l_list, trend_3s_list \
        = get_ALL_symbol_trend_data(
        symbol_base=symbol_base,
        symbol_l=symbol_l,
        symbol_s=symbol_s,
        period=period,
        size=size,
    )
    earn_value_ALL_A = 0
    earn_value_ALL_B = 0
    try:
        calculate_trend_data(
            trend_base_list=trend_base_list,
            trend_3l_list=trend_3l_list,
            trend_3s_list=trend_3s_list,
            symbol_base=symbol_base,
            start_point=1500,
            end_point=1000,
        )
        earn_value_Half_B = plan_B(symbol_base, size, int(size / 2), trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_Half_B = %s" % (symbol_base, earn_value_Half_B), ignore=False)
        earn_value_C_B = plan_B(symbol_base, int(size / 2), 1, trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_C_B = %s" % (symbol_base, earn_value_C_B), ignore=False)
        earn_value_ALL_B = plan_B(symbol_base, size, 1, trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_ALL_B = %s" % (symbol_base, earn_value_ALL_B), ignore=False)
        earn_value_Half_A = plan_A(symbol_base, size, int(size / 2), trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_Half_A = %s" % (symbol_base, earn_value_Half_A), ignore=False)
        earn_value_D_A = plan_A(symbol_base, int(size / 2), 1, trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_D_A = %s" % (symbol_base, earn_value_D_A), ignore=False)
        earn_value_ALL_A = plan_A(symbol_base, size, 1, trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_ALL_A = %s" % (symbol_base, earn_value_ALL_A), ignore=False)
        hbgAnyCall.log_print("。。。%s: ALL_A + ALL_B = %s" % (symbol_base, earn_value_ALL_A+earn_value_ALL_B), ignore=False)
        demo_print("****************************************************************************")
        calculate_trend_data(
            trend_base_list=trend_base_list,
            trend_3l_list=trend_3l_list,
            trend_3s_list=trend_3s_list,
            symbol_base=symbol_base,
            start_point=500,
            end_point=0,
        )
        earn_value_C_B_2 = plan_B(symbol_base, int(size / 4), 1, trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_C_B_2 = %s" % (symbol_base, earn_value_C_B_2), ignore=False)
        earn_value_D_A_2 = plan_A(symbol_base, int(size / 4), 1, trend_base_list, trend_3l_list, trend_3s_list)
        hbgAnyCall.log_print("%s: earn_value_D_A_2 = %s" % (symbol_base, earn_value_D_A_2), ignore=False)
    except Exception as ex:
        demo_print("Exception in calculate_base_on_KLine")
        demo_print(ex)
    return earn_value_ALL_A, earn_value_ALL_B


def plan_A(

        symbol_base, start, end,
        trend_base_list, trend_3l_list, trend_3s_list
):
    assert start > end
    pre_trend = ""
    earn_value = 0.0
    no_change_count = 0
    try:
        for i in range(start, end, -1):
            # hbgAnyCall.log_print(timeStamp_to_datetime(trend_base_list[i]["dt"]))
            if i == start:
                earn = 0
                if trend_base_list[i]["trend"] == 0:  # 平
                    no_change_count = no_change_count + 1
                    continue
                pre_trend = trend_base_list[i]["trend"]
            else:
                if trend_base_list[i]["trend"] == 0:  # 平
                    no_change_count = no_change_count + 1
                    continue
                if pre_trend != "":
                    earn = -1.0
                    if pre_trend == trend_base_list[i]["trend"]:
                        earn = 1.0
                    if pre_trend == -1:  # 跌
                        earn_value = earn_value + abs(trend_3s_list[i]["change_rate"]) * earn
                    elif pre_trend == 1:  # 涨
                        earn_value = earn_value + abs(trend_3l_list[i]["change_rate"]) * earn
                pre_trend = trend_base_list[i]["trend"]
    except Exception as ex:
        demo_print("Exception in plan_A")
        demo_print(ex)
    hbgAnyCall.log_print("%s .... earn_value = %s" % (symbol_base, earn_value))
    hbgAnyCall.log_print("%s .... no_change_count = %s" % (symbol_base, no_change_count))
    return earn_value


def plan_B(
        symbol_base, start, end,
        trend_base_list, trend_3l_list, trend_3s_list
):
    assert start > end
    pre_trend = ""
    earn_value = 0.0
    no_change_count = 0
    try:
        for i in range(start, end, -1):
            if i == start:
                earn = 0
                if trend_base_list[i]["trend"] == 0:  # 平
                    no_change_count = no_change_count + 1
                    continue
                pre_trend = trend_base_list[i]["trend"]
            else:
                if trend_base_list[i]["trend"] == 0:  # 平
                    no_change_count = no_change_count + 1
                    continue
                if pre_trend != "":
                    earn = 1.0
                    if pre_trend == trend_base_list[i]["trend"]:
                        earn = -1.0
                    if pre_trend == -1:  # 跌
                        earn_value = earn_value + abs(trend_3l_list[i]["change_rate"]) * earn
                    elif pre_trend == 1:  # 涨
                        earn_value = earn_value + abs(trend_3s_list[i]["change_rate"]) * earn
                pre_trend = trend_base_list[i]["trend"]
    except Exception as ex:
        demo_print("Exception in plan_B")
        demo_print(ex)
    hbgAnyCall.log_print("%s .... earn_value = %s" % (symbol_base, earn_value))
    hbgAnyCall.log_print("%s .... no_change_count = %s" % (symbol_base, no_change_count))
    return earn_value

# 显示交易对的K线信息的对比
def show_symbol_trend_data(
        symbol_base,
        trend_base_list,
        trend_3l_list,
        trend_3s_list
):
    assert len(trend_base_list) == len(trend_3l_list)
    assert len(trend_base_list) == len(trend_3s_list)
    list_size = len(trend_base_list)
    pre_base_trend = 0
    plan_A_value = 0
    plan_B_value = 0
    earn_A_value = 0
    earn_B_value = 0
    for i in range(list_size-1, -1, -1):
        # 时间
        demo_print(timeStamp_to_datetime(trend_base_list[i]["dt"]), end="")
        demo_print(" ", end="")
        # 趋势
        if trend_base_list[i]["trend"] >= 0:
            demo_print(" ", end="")
        demo_print(trend_base_list[i]["trend"], end="")
        demo_print(" ", end="")
        if trend_3l_list[i]["trend"] >= 0:
            demo_print(" ", end="")
        demo_print(trend_3l_list[i]["trend"], end="")
        demo_print(" ", end="")
        if trend_3s_list[i]["trend"] >= 0:
            demo_print(" ", end="")
        demo_print(trend_3s_list[i]["trend"], end="")
        demo_print(" ", end="")
        # 幅度
        int_len = 3
        precision = 8
        if trend_base_list[i]["change_rate"] >= 0:
            int_len = 2
            demo_print(" ", end="")
        demo_print(round(trend_base_list[i]["change_rate"], precision), end="")
        len_data = len(str(round(trend_base_list[i]["change_rate"], precision)))
        if len_data < precision+int_len:
            for ii in range(len_data, precision+int_len):
                demo_print(" ", end="")
        elif len_data > precision+int_len:
            if trend_base_list[i]["change_rate"] < 0:
                for ii in range(precision+int_len, len_data-1):
                    demo_print(" ", end="")
            else:
                for ii in range(precision+int_len, len_data):
                    demo_print(" ", end="")
        demo_print(" ", end="")
        int_len = 3
        if trend_3l_list[i]["change_rate"] >= 0:
            int_len = 2
            demo_print(" ", end="")
        demo_print(round(trend_3l_list[i]["change_rate"], precision), end="")
        len_data = len(str(round(trend_3l_list[i]["change_rate"], precision)))
        if len_data < precision+int_len:
            for ii in range(len_data, precision+int_len):
                demo_print(" ", end="")
        elif len_data > precision+int_len:
            if trend_3l_list[i]["change_rate"] < 0:
                for ii in range(precision+int_len, len_data-1):
                    demo_print(" ", end="")
            else:
                for ii in range(precision+int_len, len_data):
                    demo_print(" ", end="")
        demo_print(" ", end="")
        int_len = 3
        if trend_3s_list[i]["change_rate"] >= 0:
            int_len = 2
            demo_print(" ", end="")
        demo_print(round(trend_3s_list[i]["change_rate"], precision), end="")
        len_data = len(str(round(trend_3s_list[i]["change_rate"], precision)))
        if len_data < precision+int_len:
            for ii in range(len_data, precision+int_len):
                demo_print(" ", end="")
        elif len_data > precision+int_len:
            if trend_3s_list[i]["change_rate"] < 0:
                for ii in range(precision+int_len, len_data-1):
                    demo_print(" ", end="")
            else:
                for ii in range(precision+int_len, len_data):
                    demo_print(" ", end="")
        if i == list_size-1:
            demo_print("  0", end="")
            pre_base_trend = trend_base_list[i]["trend"]
        elif trend_base_list[i]["trend"] == 0:
            demo_print("  0", end="")
        else:
            earn_A = 0
            earn_B = 0
            if pre_base_trend == trend_base_list[i]["trend"]:
                demo_print("  1 -1", end="")
                earn_A = 1
                earn_B = -1
            else:
                demo_print(" -1  1", end="")
                earn_A = -1
                earn_B = 1
            earn_A_value += earn_A
            earn_B_value += earn_B
            if pre_base_trend == 1:
                plan_A_value = plan_A_value + abs(trend_3l_list[i]["change_rate"]) * earn_A
                plan_B_value = plan_B_value + abs(trend_3s_list[i]["change_rate"]) * earn_B
            elif pre_base_trend == -1:
                plan_A_value = plan_A_value + abs(trend_3s_list[i]["change_rate"]) * earn_A
                plan_B_value = plan_B_value + abs(trend_3l_list[i]["change_rate"]) * earn_B
            pre_base_trend = trend_base_list[i]["trend"]
        demo_print("  end")
    demo_print("symbol_base = %s" % symbol_base)
    demo_print("earn_A_value = %s" % earn_A_value)
    demo_print("earn_B_value = %s" % earn_B_value)
    demo_print("plan_A_value = %s" % plan_A_value)
    demo_print("plan_B_value = %s" % plan_B_value)
    return False




def demo_01():
    Total_earn_value_ALL_A = 0.0
    Total_earn_value_ALL_B = 0.0
    for etp in (
            "btc", "eth",
            "link", "eos",
            "bch", "ltc",
            "zec", "xrp",
            "bsv", "fil",
    ):
        demo_print("==========================================================")
        period = "5min"  # 1min, 5min, 15min, 30min
        demo_print("period = %s" % period)
        earn_value_ALL_A, earn_value_ALL_B = calculate_base_on_KLine(
            symbol_base=(etp+"usdt"),
            symbol_l=(etp+"3lusdt"),
            symbol_s=(etp+"3susdt"),
            period=period,  # 1min, 5min, 15min, 30min
            size=2000,
        )
        Total_earn_value_ALL_A += earn_value_ALL_A
        Total_earn_value_ALL_B += earn_value_ALL_B
    demo_print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    demo_print("Total_earn_value_ALL_A = %s " % Total_earn_value_ALL_A)
    demo_print("Total_earn_value_ALL_B = %s " % Total_earn_value_ALL_B)


def demo_03():
    response = Get_market_trade(symbol="btc3lusdt")
    print(response)

def demo_Api(access_key, secret_key):
    response = API_v2_account_repayment(access_key, secret_key)
    hbgAnyCall = HbgAnyCall()
    hbgAnyCall.print_json(response)


# def demo_02():
#     etp = "btc"
#     # etp = "bch"
#     # etp = "ltc"
#     period = "5min"
#     size = 2000
#     trend_base_list = get_symbol_trend_data(
#         symbol=(etp + "usdt"),
#         period=period,  # 1min, 5min, 15min, 30min
#         size=size,
#     )
#     trend_3l_list = get_symbol_trend_data(
#         symbol=(etp + "3lusdt"),
#         period=period,  # 1min, 5min, 15min, 30min
#         size=size,
#     )
#     trend_3s_list = get_symbol_trend_data(
#         symbol=(etp + "3susdt"),
#         period=period,  # 1min, 5min, 15min, 30min
#         size=size,
#     )
#     show_symbol_trend_data(
#         symbol_base=(etp + "usdt"),
#         trend_base_list=trend_base_list,
#         trend_3l_list=trend_3l_list,
#         trend_3s_list=trend_3s_list
#     )

# if __name__ == '__main__':
#     access_key = ACCESS_KEY
#     secret_key = SECRET_KEY
#     account_id = ACCOUNT_ID  # spot
#     hbgAnyCall = HbgAnyCall()
#     try:
#         # demo_01()
#         # demo_02()
#         demo_03()
#         # demo_Api(access_key, secret_key)
#     except Exception as ex:
#         demo_print("Exception in main")
#         hbgAnyCall.log_print(ex, ignore=False)


        # 下单
        # response = Post_order_place(
        #     access_key=access_key, secret_key=secret_key,
        #     account_id=account_id,
        #     symbol="btc3lusdt",
        #     type_value="buy-market",
        #     amount="10",
        #     client_order_id="demo_001"
        # )
        # hbgAnyCall.log_print("下单 [Response]")
        # hbgAnyCall.print_json(response)
        # 获取指定币种的账户余额
        # currency = "btc3l"
        # balance = get_currency_balance(
        #     access_key=access_key, secret_key=secret_key,
        #     account_id=account_id,
        #     currency=currency,
        #     type_value="trade"
        # )
        # hbgAnyCall.log_print("币种 %s 的现货可用账户余额是 %s " % (currency, balance))
        # 交易明细
        # response = Get_orders_matchresults(
        #     access_key=access_key, secret_key=secret_key,
        #     order_id="186111551550078",
        # )
        # hbgAnyCall.log_print("交易明细 [Response]")
        # hbgAnyCall.print_json(response)
        # response = Get_etp_limit(
        #     access_key=access_key, secret_key=secret_key,
        #     currency="btc3l,eth1s",
        # )
        # hbgAnyCall.log_print("[Response]")
        # hbgAnyCall.print_json(response)

      # hbgAnyCall.log_print(
        #     "%s    %s    %s      %s%%     %s      %s%%       %s      %s%%" %
        #     (
        #         timeStamp_to_datetime(trend_base_list[i]["dt"]),
        #         trend_base_list[i]["trend"], earn,
        #         round(trend_base_list[i]["change_rate"]*100.0, 4),
        #         #timeStamp_to_datetime(trend_3l_list[i]["dt"]),
        #         #trend_3l_list[i]["symbol"],
        #         trend_3l_list[i]["trend"],
        #         round(trend_3l_list[i]["change_rate"]*100.0, 4),
        #         #timeStamp_to_datetime(trend_3s_list[i]["dt"]),
        #         #trend_3s_list[i]["symbol"],
        #         trend_3s_list[i]["trend"],
        #         round(trend_3s_list[i]["change_rate"]*100.0, 4)
        #     )
        # )