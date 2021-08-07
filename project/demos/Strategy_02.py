from decimal import *
import math
import datetime
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
import logging
import time
import multiprocessing
from multiprocessing import Pool, Manager
from project.demos.config import *
from project.demos.Strategy_Base import *

# 合约的策略
class Strategy_02(Strategy_Base):
    holding_base_amount = 0.0  # 当前持有的 Base 的数量
    cur_buy_base_amount = 0.0  # 最近一次购入的 Base 的数量
    cur_buy_base_price = 0.0  # 最近一次购入的 Base 的价格
    cur_buy_quoter_amount = 0.0  # 最近一次购入 BASE 成功后，花费的 quoter 的数量
    cur_buy_base_fees_amount = 0.0  # 最近一次购入 BASE 成功后，花费的 手续费 base 的数量
    quoter_total_cost = 0.0  # 投入的总成本(quoter)
    max_quoter_total_cost = 0.0  # 投入的最高总成本(quoter)
    holding_quoter_amount = 5000.0  # 当前持有的 quoter 的数量
    quoter_accumulated_income = 0.0  # 当前累计的 quoter 收益
    increasing_price_rate = 0.01  # 下限价卖单时的价格增加率
    sell_limit_order_list = []  # 当前未成交的限价卖单列表
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    strategy_launch_time = 0
    reference_period = "1day"  # "60min"

    test_k_line_data_list = []
    test_k_line_data_index = 999  # 1999

    def init_all(self):
        self.holding_base_amount = 0.0  # 当前持有的 Base 的数量
        self.cur_buy_base_amount = 0.0  # 最近一次购入的 Base 的数量
        self.cur_buy_base_price = 0.0  # 最近一次购入的 Base 的价格
        self.quoter_total_cost = 0.0  # 投入的总成本(quoter)
        self.max_quoter_total_cost = 0.0  # 投入的最高总成本(quoter)
        self.holding_quoter_amount = 5000.0  # 当前持有的 quoter 的数量
        self.quoter_accumulated_income = 0.0  # 当前累计的 quoter 收益
        self.increasing_price_rate = 0.01  # 下限价卖单时的价格增加率
        self.sell_limit_order_list = []  # 当前未成交的限价卖单列表

        self.test_k_line_data_list = []
        self.test_k_line_data_index = 999  # 1999

    def init_test_k_line_data_list(self, symbol, period="5min"):
        ret_data = self.get_kline_data(
            symbol=symbol,
            period=period,
            size=self.test_k_line_data_index+1
        )
        for ret_item in ret_data:
            k_line_data = {
                "change": "up",
                "open_price": ret_item["open"],
                "close_price": ret_item["close"],
                "high_price": ret_item["high"],
                "low_price": ret_item["low"],
                "dt": TimeStamp_to_datetime(timeStamp=ret_item["id"])
            }
            if float(ret_item["close"]) < float(ret_item["open"]):
                k_line_data["change"] = "down"
            self.test_k_line_data_list.append(k_line_data)
        return True

    # 模拟买入Base
    def simulate_buy_base(self, k_line_data):
        try:
            cur_open = k_line_data["open_price"]
            self.cur_buy_base_amount = self.buy_min_quoter_amount / float(cur_open)
            # 当前持有的 Base 的数量 增加
            self.holding_base_amount += self.cur_buy_base_amount
            # 投入的总成本(quoter) 增加
            self.quoter_total_cost += self.buy_min_quoter_amount
            if self.max_quoter_total_cost < self.quoter_total_cost:
                self.max_quoter_total_cost = self.quoter_total_cost
            # 当前持有的 quoter 的数量 减少
            self.holding_quoter_amount -= self.buy_min_quoter_amount
            return True
        except Exception as ex:
            self.log_print("Exception in simulate_buy_base!")
            self.log_print("ex: %s" % ex)
            return False

    # 处理成交的限价卖单
    def simulate_dispose_sell_limit_orders(self, pre_1_k_line_data):
        last_high_price = pre_1_k_line_data["high_price"]
        for sell_limit_order in self.sell_limit_order_list:
            if not sell_limit_order["finish"] and sell_limit_order["price"] < last_high_price:  # 限价卖单已经成交
                cur_quoter_income = float(sell_limit_order["amount"]) * float(sell_limit_order["price"])
                # 当前持有的 Base 的数量 减少
                self.holding_base_amount -= self.cur_buy_base_amount
                # 投入的总成本(quoter) 减少
                self.quoter_total_cost -= self.buy_min_quoter_amount
                # 当前持有的 quoter 的数量 增加
                self.holding_quoter_amount += cur_quoter_income
                # 当前累计的 quoter 收益 增加
                self.quoter_accumulated_income += (cur_quoter_income - self.buy_min_quoter_amount)
                # 标记限价卖单已成交
                sell_limit_order["finish"] = True
        return True

    # 买入合约
    def buy_contract(self, k_line_data, invest_direction):
        try_count = 0
        b_SuccessToBuy = False
        try:
            # 如果余额不足，则直接返回
            account_banlance = self.get_accounts_balance()
            if account_banlance:
                if account_banlance < self.buy_min_quoter_amount:
                    self.log_print("当前 usdt 余额 %s 小于 最小投资额 %s , 暂停投资。"
                                   % (account_banlance, self.buy_min_quoter_amount))
                    return False
            while not b_SuccessToBuy and try_count < 5:
                try_count += 1
                b_SuccessToBuy = self.try_buy_contract(
                    k_line_data=k_line_data,
                    invest_direction=invest_direction
                )
                if b_SuccessToBuy:
                    self.log_print("Success to BUY !")
                    break
                else:
                    time.sleep(2)
                    self.log_print("Fail to BUY ! try %s times" % try_count)
            if b_SuccessToBuy:
                # 当前持有的 Base 的数量 增加
                self.holding_base_amount += self.cur_buy_base_amount
                # 投入的总成本(quoter) 增加
                self.quoter_total_cost += self.cur_buy_quoter_amount
                if self.max_quoter_total_cost < self.quoter_total_cost:
                    self.max_quoter_total_cost = self.quoter_total_cost
                # 当前持有的 quoter 的数量 减少
                self.holding_quoter_amount -= self.buy_min_quoter_amount
            return b_SuccessToBuy
        except Exception as ex:
            self.log_print("Exception in buy_base!")
            self.log_print("ex: %s" % ex)
            return False

    # 尝试买入合约
    def try_buy_contract(self, k_line_data, invest_direction):
        bSuccessToBuy = False
        cur_buy_base_price = 0.0
        cur_buy_base_amount = 0.0
        cur_buy_quoter_amount = 0.0
        cur_buy_base_fees_amount = 0.0
        try:
            buy_min_quoter_amount = self.buy_min_quoter_amount
            status = "error"
            retry_count = 0
            contract_volume = 1
            direction_value = "buy"
            contract_price = 0.0
            if invest_direction != "up":
                direction_value = "sell"
            while status != "ok" and retry_count < MAX_RETRY_COUNT:
                retry_count += 1
                ret = Post_LinearSwapApi_v1_SwapCross_Order(
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    contract_code=self.symbol,  # 合约代码
                    price=None,  # 价格
                    volume=contract_volume,  # 委托数量(张)
                    direction=direction_value,  # 仓位方向
                    offset="open",  # 开平方向
                    lever_rate=3,  # 杠杆倍数
                    order_price_type="post_only",  # 订单报价类型
                    tp_trigger_price=None,  # 止盈触发价格
                    tp_order_price=None,  # 止盈委托价格
                    tp_order_price_type=None,  # 止盈委托类型
                    sl_trigger_price=None,  # 止损触发价格
                    sl_order_price=None,  # 止损委托价格
                    sl_order_price_type=None  # 止损委托类型
                )
                status = ret["status"]
                if status != "ok":
                    time.sleep(1)
            if status == "ok":
                bSuccessToBuy = True
            ret_data = ret["data"]
        except Exception as ex:
            self.log_print("Ex IN try_buy_contract: %s" % ex)
            bSuccessToBuy = False
        if bSuccessToBuy:
            self.cur_buy_base_price = cur_buy_base_price
            self.cur_buy_base_amount = cur_buy_base_amount
            self.cur_buy_quoter_amount = cur_buy_quoter_amount
            self.cur_buy_base_fees_amount = cur_buy_base_fees_amount
        return bSuccessToBuy


    # 处理已经成交的合约订单
    def dispose_fufilled_contract_order(self, pre_1_k_line_data):
        last_high_price = pre_1_k_line_data["high_price"]
        b_show = False
        for sell_limit_order in self.sell_limit_order_list:
            if not sell_limit_order["finish"] and sell_limit_order["price"] < last_high_price:  # 限价卖单已经成交
                cur_quoter_income = float(sell_limit_order["amount"]) * float(sell_limit_order["price"])
                # 当前持有的 Base 的数量 减少
                self.holding_base_amount -= self.cur_buy_base_amount
                # 投入的总成本(quoter) 减少
                self.quoter_total_cost -= cur_quoter_income
                # 当前持有的 quoter 的数量 增加
                self.holding_quoter_amount += cur_quoter_income
                # 当前累计的 quoter 收益 增加
                self.quoter_accumulated_income += (cur_quoter_income - self.cur_buy_quoter_amount)
                # 标记限价卖单已成交
                sell_limit_order["finish"] = True
                self.show_current_profit_and_loss()
                b_show = True
        if not b_show:
            self.log_print("No Income ......")
        return True

    # 显示当前的盈亏
    def show_current_profit_and_loss(self, cur_status="Income"):
        self.log_print("\n################## %s ##################" % cur_status)
        self.log_print("币种: %s" % self.symbol)
        period_int = get_period_int(self.period)
        self.log_print("时间间隔: %s 分钟" % period_int)
        self.log_print("计划运行时长: %s 天" % self.run_days)
        self.log_print("启动时间: %s " %
                       TimeStamp_to_datetime(self.strategy_launch_time))
        delta_time = math.trunc(time.time()) - self.strategy_launch_time
        self.log_print("已运行时长: %s " % Show_delta_time(delta_time=delta_time))
        self.log_print("下限价卖单时的价格增加率: %s" % self.increasing_price_rate)
        self.log_print("每次投入 quoter 数量: %s" % self.buy_min_quoter_amount)
        self.log_print("当前持有的 Base 的数量: %s" % self.holding_base_amount)
        self.log_print("最近一次购入的 Base 的数量: %s" % self.cur_buy_base_amount)
        self.log_print("投入的总成本: %s" % self.quoter_total_cost)
        self.log_print("投入的最高总成本: %s" % self.max_quoter_total_cost)
        self.log_print("当前持有的 quoter 的数量: %s" % self.holding_quoter_amount)
        self.log_print("当前累计的 quoter 收益: %s" % self.quoter_accumulated_income)
        count = 0
        for item in self.sell_limit_order_list:
            if not item["finish"]:
                count += 1
        self.log_print("当前限价卖单的挂单量: %s" % count)
        self.log_print("已经成交的限价卖单的挂单量: %s" % (len(self.sell_limit_order_list) - count))
        if self.quoter_total_cost > 0.0:
            income_rate = float(self.quoter_accumulated_income) / float(self.quoter_total_cost)
            self.log_print("当前的收益率: %s%%" % (income_rate * 100.0))
            if delta_time != 0.0:
                already_run_days = delta_time / (24*60*60)
                income_rate_by_day = income_rate / already_run_days
                self.log_print("日均收益率: %s%%" % (income_rate_by_day * 100.0))
        self.log_print("\n################## %s ##################\n" % cur_status)
        return True

    # 获取指定币种的可用余额
    def get_accounts_balance(
            self,
            currency="usdt",
            type_value="trade"
    ):
        try:
            accounts_balance = 0.0
            b_find = False
            count = 0
            while count < 5:
                count += 1
                ret = Get_v1_account_accounts_accountId_balance(
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    accountId=self.account_id,
                )
                if ret["status"] != "ok":
                    time.sleep(2)
                else:
                    assert ret["data"]["id"] == int(self.account_id)
                    data_list = ret["data"]["list"]
                    for item in data_list:
                        if item["currency"] == currency and item["type"] == type_value:
                            accounts_balance = float(item["balance"])
                            b_find = True
                            break
                    break
            if b_find:
                ret_value = accounts_balance
            else:
                ret_value = False
            return ret_value
        except Exception as ex:
            self.log_print("Exception in get_accounts_balance!")
            self.log_print("ex: %s" % ex)
            return False

    # 获取最近一次参考价
    def get_last_reference_price(self, reference_period="60min"):
        OK, ret_data = self.get_LinearSwapEx_Market_History_Kline(
            symbol=self.symbol,
            period=reference_period,
            size=1
        )
        if OK:
            ret_item = ret_data[0]
            last_reference_price_data = {
                "open_price": float(ret_item["open"]),
                "dt": TimeStamp_to_datetime(timeStamp=ret_item["id"])
            }
        else:
            self.log_print("Failed to get_last_reference_price! ")
            last_reference_price_data = None
        return last_reference_price_data

    # 依据参考价判定投资与否和投资方向
    def is_suitable_for_investment(self, cur_price, reference_period="1day"):
        be_suitable = False
        invest_direction = ""
        last_reference_price_data \
            = self.get_last_reference_price(reference_period=reference_period)
        if last_reference_price_data is not None:
            last_reference_price = last_reference_price_data["open_price"]
            last_reference_dt = last_reference_price_data["dt"]
            self.log_print("IN is_suitable_for_investment, cur_price: %s " % cur_price)
            self.log_print("IN is_suitable_for_investment, last_reference_price: %s " % last_reference_price)
            self.log_print("IN is_suitable_for_investment, last_reference_dt: %s " % last_reference_dt)
            if cur_price > last_reference_price:
                be_suitable = True
                invest_direction = "up"
            elif cur_price == last_reference_price:
                be_suitable = False
                invest_direction = ""
            else:  # cur_price < last_reference_price
                be_suitable = True
                invest_direction = "down"
            self.log_print("IN is_suitable_for_investment, be_suitable = %s, invest_direction = %s"
                           % (be_suitable, invest_direction))
        return be_suitable, invest_direction

    # 获取合约近3次的K线数据
    def get_3_kline_data(self, symbol, period="5min"):
        self.wait_to_next_X_min_begin(x=get_period_int(period))
        ret_data = self.get_LinearSwapEx_Market_History_Kline(
            symbol=symbol,
            period=period,
            size=3
        )
        k_line_data_list = []
        for ret_item in ret_data:
            k_line_data = {
                "change": "up",
                "open_price": ret_item["open"],
                "close_price": ret_item["close"],
                "high_price": ret_item["high"],
                "low_price": ret_item["low"],
                "dt": TimeStamp_to_datetime(timeStamp=ret_item["id"])
            }
            if float(ret_item["close"]) < float(ret_item["open"]):
                k_line_data["change"] = "down"
            k_line_data_list.append(k_line_data)
        return k_line_data_list

    def get_3_kline_data_2(self, symbol="ethusdt", period="5min"):
        k_line_data_list = []
        if self.test_k_line_data_index >= 2:
            k_line_data_list.append(self.test_k_line_data_list[self.test_k_line_data_index - 2])
            k_line_data_list.append(self.test_k_line_data_list[self.test_k_line_data_index - 1])
            k_line_data_list.append(self.test_k_line_data_list[self.test_k_line_data_index])
            self.test_k_line_data_index -= 1
        else:
            k_line_data_list.append(self.test_k_line_data_list[0])
            k_line_data_list.append(self.test_k_line_data_list[1])
            k_line_data_list.append(self.test_k_line_data_list[2])
        return k_line_data_list

    def simulate_do_strategy_execute(self, symbol, period, buy_min_quoter_amount, dt_stamp):
        try:
            self.symbol = symbol
            self.buy_min_quoter_amount = buy_min_quoter_amount
            self.logger_init(
                log_folder_name="Strategy_01_log",
                log_file_template="/Strategy_01_%s_%s.log",
                dt_stamp=dt_stamp
            )
            while self.test_k_line_data_index >= 2:
                k_line_data_list = self.get_3_kline_data_2(symbol=symbol, period=period)
                # 处理成交的限价卖单
                self.simulate_dispose_sell_limit_orders(pre_1_k_line_data=k_line_data_list[1])
                # 根据K线价格来投资
                pre_2_change = k_line_data_list[2]["change"]
                pre_1_change = k_line_data_list[1]["change"]
                bInvestCoin = False
                if pre_2_change == "down" and pre_1_change == "up":
                    bInvestCoin = True
                elif pre_2_change == "up" and pre_1_change == "up":
                    bInvestCoin = True
                if bInvestCoin:
                    cur_k_line_data = k_line_data_list[0]
                    # 模拟买入Base
                    self.simulate_buy_base(k_line_data=cur_k_line_data)
        except Exception as ex:
            self.log_print("Exception in simulate_do_strategy_execute")
            self.log_print("ex: %s" % ex)

    # 执行策略
    def do_strategy_execute(self, symbol, period, run_days, buy_min_quoter_amount, dt_stamp):
        try:
            self.symbol = symbol
            self.period = period
            self.run_days = run_days
            self.buy_min_quoter_amount = buy_min_quoter_amount
            self.logger_init(
                log_folder_name="Strategy_01_log",
                log_file_template="/Strategy_01_%s_%s.txt",
                dt_stamp=dt_stamp
            )
            self.strategy_launch_time = int(time.time())
            run_time_config_data = self.get_run_time_configuration()
            self.buy_min_quoter_amount = run_time_config_data["buy_min_quoter_amount"]
            self.increasing_price_rate = run_time_config_data["increasing_price_rate"]
            self.period = run_time_config_data["period"]
            while not run_time_config_data["quit"]:
                if run_time_config_data["keep_run"]:
                    k_line_data_list = self.get_3_kline_data(symbol=symbol, period=period)
                    # 处理已经成交的合约订单
                    self.dispose_fufilled_contract_order(pre_1_k_line_data=k_line_data_list[1])
                    # 依据参考价判定投资与否和投资方向
                    be_suitable_for_investment, invest_direction = self.is_suitable_for_investment(
                        cur_price=float(k_line_data_list[0]["open_price"]),
                        reference_period=self.reference_period
                    )
                    if not be_suitable_for_investment:
                        # 如果现在不宜投资，则暂时放弃。
                        continue
                    # 根据K线价格来投资
                    pre_2_change = k_line_data_list[2]["change"]
                    pre_1_change = k_line_data_list[1]["change"]
                    bInvestCoin = False
                    if invest_direction == "up":
                        if pre_2_change == "down" and pre_1_change == "up":
                            bInvestCoin = True
                        elif pre_2_change == "up" and pre_1_change == "up":
                            bInvestCoin = True
                    else:  # invest_direction == "down"
                        if pre_2_change == "up" and pre_1_change == "down":
                            bInvestCoin = True
                        elif pre_2_change == "down" and pre_1_change == "down":
                            bInvestCoin = True
                    if bInvestCoin:
                        cur_k_line_data = k_line_data_list[0]
                        # 买入合约
                        OK = self.buy_contract(
                            k_line_data=cur_k_line_data,
                            invest_direction=invest_direction
                        )
                        if not OK:
                            continue
                else:
                    time.sleep(2)
                run_time_config_data = self.get_run_time_configuration()
                self.buy_min_quoter_amount = run_time_config_data["buy_min_quoter_amount"]
                self.increasing_price_rate = run_time_config_data["increasing_price_rate"]
                self.period = run_time_config_data["period"]
            self.log_print("$$$$$$$$$$$$$$ The Strategy Quit $$$$$$$$$$$$$$$$")
        except Exception as ex:
            self.log_print("Exception in do_strategy_execute")
            self.log_print("ex: %s" % ex)

    # 获取运行时的配置信息
    def get_run_time_configuration(self):
        run_time_config_data = read_yaml(
            filename="run_time_config_Strategy_01.yaml"
        )
        return run_time_config_data["run_time_config"]["symbol_list"][self.symbol]


def get_period_int(period):
    period_int = 5
    if period == "5min":
        period_int = 5
    elif period == "15min":
        period_int = 15
    elif period == "30min":
        period_int = 30
    elif period == "60min":
        period_int = 60
    elif period == "4hour":
        period_int = 4*60
    elif period == "1day":
        period_int = 24*60
    return period_int

def earn_method(symbol, period, size, buy_min_quoter_amount, increasing_price_rate):
    time_stamp = int(time.time())
    dt_stamp = TimeStamp_to_datetime(time_stamp)
    my_strategy = Strategy_01()
    my_strategy.init_all()
    my_strategy.test_k_line_data_index = size - 1
    my_strategy.increasing_price_rate = increasing_price_rate
    my_strategy.init_test_k_line_data_list(
        symbol=symbol,
        period=period
    )
    my_strategy.simulate_do_strategy_execute(
        symbol=symbol,
        period=period,
        buy_min_quoter_amount=buy_min_quoter_amount,
        dt_stamp=dt_stamp
    )
    print("币种: %s" % symbol)
    period_int = get_period_int(period)
    print("时间间隔: %s 分钟" % period_int)
    run_days = period_int * size / 60 / 24
    print("计算时长: %s 天" % run_days)
    print("下限价卖单时的价格增加率: %s" % my_strategy.increasing_price_rate)
    print("每次投入 quoter 数量: %s" % my_strategy.buy_min_quoter_amount)
    print("当前持有的 Base 的数量: %s" % my_strategy.holding_base_amount)
    print("最近一次购入的 Base 的数量: %s" % my_strategy.cur_buy_base_amount)
    print("当前投入的总成本: %s" % my_strategy.quoter_total_cost)
    print("投入的最高总成本: %s" % my_strategy.max_quoter_total_cost)
    print("当前持有的 quoter 的数量: %s" % my_strategy.holding_quoter_amount)
    print("当前累计的 quoter 收益: %s" % my_strategy.quoter_accumulated_income)
    count = 0
    for item in my_strategy.sell_limit_order_list:
        if not item["finish"]:
            count += 1
    print("当前限价卖单的挂单量: %s" % count)
    print("已经成交的限价卖单的挂单量: %s" % (len(my_strategy.sell_limit_order_list) - count))
    income_rate = float(my_strategy.quoter_accumulated_income) / float(my_strategy.quoter_total_cost)
    print("当前的收益率: (当前累计的 quoter 收益)/(当前投入的总成本)\n%s%%" % (income_rate * 100.0))
    income_rate_by_day = income_rate / run_days
    print("日均收益率: %s%%" % (income_rate_by_day * 100.0))
    income_by_day = my_strategy.quoter_accumulated_income / run_days
    print("日均收益: %s" % income_by_day)
    return (
        my_strategy.quoter_total_cost,
        my_strategy.quoter_accumulated_income,
        income_rate,
        income_rate_by_day
    )


def bench_earn_money():
    symbol_list = [
        #{"symbol": "btcusdt", "increasing_price_rate": 0.01},
        {"symbol": "ethusdt", "increasing_price_rate": 0.01},
        {"symbol": "sushiusdt", "increasing_price_rate": 0.01},
        {"symbol": "linkusdt", "increasing_price_rate": 0.01},
        {"symbol": "uniusdt", "increasing_price_rate": 0.01},
        #{"symbol": "dotusdt", "increasing_price_rate": 0.01},
        #{"symbol": "linkusdt", "increasing_price_rate": 0.01},
        #{"symbol": "ltcusdt", "increasing_price_rate": 0.01},
    ]
    total_quoter_total_cost = 0.0
    total_quoter_accumulated_income = 0.0
    total_income_rate = 0.0
    total_income_rate_by_day = 0.0
    period = "5min"
    # period = "15min"
    # period = "30min"
    # period = "60min"
    # period = "4hour"
    size = int(6*24*60/5)
    buy_min_quoter_amount = 6.0  #* 12 * 4
    # buy_min_quoter_amount = 4*60.0
    for symbol_item in symbol_list:
        (
            quoter_total_cost,
            quoter_accumulated_income,
            income_rate,
            income_rate_by_day
        ) = earn_method(
            symbol=symbol_item["symbol"],
            period=period,
            size=size,
            buy_min_quoter_amount=buy_min_quoter_amount,
            increasing_price_rate=symbol_item["increasing_price_rate"],  # 下限价卖单时的价格增加率
        )
        print("==============================")
        total_quoter_total_cost += quoter_total_cost
        total_quoter_accumulated_income += quoter_accumulated_income
        total_income_rate += income_rate
        total_income_rate_by_day += income_rate_by_day
    print("==============================")
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    time_stamp = int(time.time())
    dt_stamp = TimeStamp_to_datetime(
        timeStamp=time_stamp,
        dt_format="%Y年%m月%d日 %H时%M分%S秒"
    )
    print("统计时间: %s" % dt_stamp)
    period_int = get_period_int(period)
    print("时间间隔: %s 分钟" % period_int)
    run_days = period_int * size / 60 / 24
    print("计算时长: %s 天" % run_days)
    print("单次投资额: %s USDT" % buy_min_quoter_amount)
    print("合计——投入的总成本: %s" % total_quoter_total_cost)
    print("合计——当前累计的 quoter 收益: %s" % total_quoter_accumulated_income)
    avg_income_rate = float(total_income_rate) / float(len(symbol_list))
    print("合计——当前的收益率: %s%%" % (avg_income_rate * 100.0))
    avg_income_rate_by_day = float(total_income_rate_by_day) / float(len(symbol_list))
    print("合计——日均收益率: %s%%" % (avg_income_rate_by_day * 100.0))


def try_buy_coins():
    try:
        bSuccessToBuy = False
        symbol = "ethusdt"
        buy_min_quoter_amount = 6.0
        # 询价
        ret = Get_market_depth(
            symbol=symbol
        )
        first_buy_price = ret["tick"]["bids"][0][0]
        print("first_buy_price: %s" % first_buy_price)
        first_sell_price = ret["tick"]["asks"][0][0]
        print("first_sell_price: %s" % first_sell_price)
        cur_buy_base_price = (float(first_buy_price) + float(first_sell_price)) / 2.0
        cur_buy_base_amount = buy_min_quoter_amount / float(cur_buy_base_price)
        cur_buy_base_price = round(cur_buy_base_price, get_price_precision(symbol))
        cur_buy_base_amount = round(cur_buy_base_amount, get_amount_precision(symbol))
        print("cur_buy_base_price: %s" % cur_buy_base_price)
        print("cur_buy_base_amount: %s" % cur_buy_base_amount)
        # 下限价买单
        ret = Post_order_place(
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            account_id=ACCOUNT_ID,
            symbol=symbol,
            type_value="buy-limit",
            amount=cur_buy_base_amount,
            price=cur_buy_base_price
        )
        assert ret["status"] == "ok"
        # 查询订单状态
        order_id = ret["data"]
        print("order_id: %s" % order_id)
        ret = Get_v1_order_orders_orderId(
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            order_id=order_id,
        )
        assert ret["status"] == "ok"
        order_state = ret["data"]["state"]
        print("order_state:%s " % order_state)
        if order_state == "filled":
            bSuccessToBuy = True
        else:
            count = 0
            while order_state != "filled" and count < 5:
                print("order_state: %s " % order_state)
                print("cancel order: count= %s " % count)
                count += 1
                time.sleep(2)
                ret = Get_v1_order_orders_orderId(
                    access_key=ACCESS_KEY,
                    secret_key=SECRET_KEY,
                    order_id=order_id,
                )
                assert ret["status"] == "ok"
                order_state = ret["data"]["state"]
            if order_state != "filled":
                # 撤单
                ret = Post_v1_order_orders_orderId_submitcancel(
                    access_key=ACCESS_KEY,
                    secret_key=SECRET_KEY,
                    order_id=order_id,
                )
                assert ret["status"] == "ok"
                assert ret["data"] == str(order_id)
            else:
                bSuccessToBuy = True
    except Exception as ex:
        print("Ex IN try_buy_coins: %s" % ex)
        bSuccessToBuy = False
    return bSuccessToBuy



if __name__ == '__main__':
    bench_earn_money()