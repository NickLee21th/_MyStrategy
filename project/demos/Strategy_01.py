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


class Strategy_01(Strategy_Base):
    holding_base_amount = 0.0  # 当前持有的 Base 的数量
    cur_buy_base_amount = 0.0  # 最近一次购入的 Base 的数量
    cur_buy_base_price = 0.0  # 最近一次购入的 Base 的价格
    cur_buy_quoter_amount = 0.0  # 最近一次购入 BASE 成功后，花费的 quoter 的数量
    cur_buy_base_fees_amount = 0.0  # 最近一次购入 BASE 成功后，花费的 手续费 base 的数量
    quoter_total_cost = 0.0  # 投入的总成本(quoter)
    holding_quoter_amount = 5000.0  # 当前持有的 quoter 的数量
    quoter_accumulated_income = 0.0  # 当前累计的 quoter 收益
    increasing_price_rate = 0.01  # 下限价卖单时的价格增加率
    sell_limit_order_list = []  # 当前未成交的限价卖单列表
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    strategy_launch_time = 0

    test_k_line_data_list = []
    test_k_line_data_index = 999  # 1999

    def init_all(self):
        self.holding_base_amount = 0.0  # 当前持有的 Base 的数量
        self.cur_buy_base_amount = 0.0  # 最近一次购入的 Base 的数量
        self.cur_buy_base_price = 0.0  # 最近一次购入的 Base 的价格
        self.quoter_total_cost = 0.0  # 投入的总成本(quoter)
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
            # 当前持有的 quoter 的数量 减少
            self.holding_quoter_amount -= self.buy_min_quoter_amount
            return True
        except Exception as ex:
            self.log_print("Exception in simulate_buy_base!")
            self.log_print("ex: %s" % ex)
            return False

    # 模拟下限价卖单
    def simulate_place_sell_limit(self, k_line_data):
        try:
            cur_open = k_line_data["open_price"]
            price_in_sell_limit = float(cur_open) * (1.0 + self.increasing_price_rate)
            sell_limit_order = {
                "price": price_in_sell_limit,
                "amount": self.cur_buy_base_amount,
                "finish": False
            }
            self.sell_limit_order_list.append(sell_limit_order)
            return True
        except Exception as ex:
            self.log_print("Exception in simulate_place_sell_limit!")
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

    # 买入Base
    def buy_base(self, k_line_data):
        try_count = 0
        b_SuccessToBuy = False
        try:
            while not b_SuccessToBuy and try_count < 5:
                try_count += 1
                b_SuccessToBuy = self.try_buy_coins()
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
                # 当前持有的 quoter 的数量 减少
                self.holding_quoter_amount -= self.buy_min_quoter_amount
            return b_SuccessToBuy
        except Exception as ex:
            self.log_print("Exception in buy_base!")
            self.log_print("ex: %s" % ex)
            return False

    # 尝试买入 Base
    def try_buy_coins(self):
        bSuccessToBuy = False
        cur_buy_base_price = 0.0
        cur_buy_base_amount = 0.0
        cur_buy_quoter_amount = 0.0
        cur_buy_base_fees_amount = 0.0
        try:
            buy_min_quoter_amount = self.buy_min_quoter_amount
            # 询价
            ret = Get_market_depth(
                symbol=self.symbol
            )
            if ret["status"] != "ok":
                self.log_print(" ret_status: %s  \n ret: %s "
                               % (ret["status"], ret))
                raise Exception("Failed in Get_market_depth")
            first_buy_price = ret["tick"]["bids"][0][0]
            first_sell_price = ret["tick"]["asks"][0][0]
            cur_buy_base_price = (float(first_buy_price) + float(first_sell_price)) / 2.0
            cur_buy_base_amount = buy_min_quoter_amount / float(cur_buy_base_price)
            cur_buy_base_price = round(cur_buy_base_price, get_price_precision(self.symbol))
            cur_buy_base_amount = round(cur_buy_base_amount, get_amount_precision(self.symbol))
            # 下限价买单
            ret = Post_order_place(
                access_key=self.access_key,
                secret_key=self.secret_key,
                account_id=self.account_id,
                symbol=self.symbol,
                type_value="buy-limit",
                amount=cur_buy_base_amount,
                price=cur_buy_base_price
            )
            if ret["status"] != "ok":
                self.log_print(" ret_status: %s  \n ret: %s "
                               % (ret["status"], ret))
                raise Exception("Failed in Post_order_place")
            # 查询订单状态
            order_id = ret["data"]
            self.log_print("IN try_buy_coins, order_id: %s" % order_id)
            ret = Get_v1_order_orders_orderId(
                access_key=ACCESS_KEY,
                secret_key=SECRET_KEY,
                order_id=order_id,
            )
            if ret["status"] != "ok":
                self.log_print(" ret_status: %s  \n ret: %s "
                               % (ret["status"], ret))
                raise Exception("Failed in Get_v1_order_orders_orderId")
            order_state = ret["data"]["state"]
            self.log_print("IN try_buy_coins, order_state:%s " % order_state)
            if order_state == "filled":
                bSuccessToBuy = True
            else:
                count = 0
                while order_state != "filled" and count < 5:
                    self.log_print("IN try_buy_coins, order_state: %s " % order_state)
                    self.log_print("IN try_buy_coins, retry count= %s " % count)
                    count += 1
                    time.sleep(2)
                    ret = Get_v1_order_orders_orderId(
                        access_key=ACCESS_KEY,
                        secret_key=SECRET_KEY,
                        order_id=order_id,
                    )
                    if ret["status"] != "ok":
                        self.log_print(" ret_status: %s  \n ret: %s "
                                       % (ret["status"], ret))
                        raise Exception("Failed in Get_v1_order_orders_orderId")
                    order_state = ret["data"]["state"]
                if order_state != "filled":
                    # 撤单
                    self.log_print("IN try_buy_coins, cancel order: %s " % order_id)
                    ret = Post_v1_order_orders_orderId_submitcancel(
                        access_key=ACCESS_KEY,
                        secret_key=SECRET_KEY,
                        order_id=order_id,
                    )
                    if ret["status"] != "ok":
                        self.log_print(" ret_status: %s  \n ret: %s "
                                       % (ret["status"], ret))
                        raise Exception("Failed in Post_v1_order_orders_orderId_submitcancel")
                    assert ret["status"] == "ok"
                    assert ret["data"] == str(order_id)
                else:
                    bSuccessToBuy = True
            if bSuccessToBuy:
                # 买入成功后，记录买入 base 的价格
                cur_buy_base_price = float(ret["data"]["price"])
                # 买入成功后，记录买入 base 的数量
                cur_buy_base_amount = float(ret["data"]["field-amount"])
                # 买入成功后，记录花费的 quoter 的数量
                cur_buy_quoter_amount = float(ret["data"]["field-cash-amount"])
                # 买入成功后，记录花费的 手续费 base 的数量
                cur_buy_base_fees_amount = float(ret["data"]["field-fees"])
        except Exception as ex:
            self.log_print("Ex IN try_buy_coins: %s" % ex)
            bSuccessToBuy = False
        if bSuccessToBuy:
            self.cur_buy_base_price = cur_buy_base_price
            self.cur_buy_base_amount = cur_buy_base_amount
            self.cur_buy_quoter_amount = cur_buy_quoter_amount
            self.cur_buy_base_fees_amount = cur_buy_base_fees_amount
        return bSuccessToBuy

    # 下限价卖单
    def place_sell_limit(self):
        try:
            price_in_sell_limit = float(self.cur_buy_base_price) * (1.0 + self.increasing_price_rate)
            amount = round(self.cur_buy_base_amount, get_amount_precision(self.symbol))
            price_in_sell_limit = round(price_in_sell_limit, get_price_precision(self.symbol))
            self.log_print("下限价卖单, 价格： %s , 数量：%s " % (price_in_sell_limit, amount))
            self.log_print("限价卖单成交后，可以获取 %s  USDT 收入。" % (price_in_sell_limit * amount))
            self.log_print("买入BASE时，花费的成本是 %s USDT " % self.cur_buy_quoter_amount)
            assert (price_in_sell_limit * amount) > self.cur_buy_quoter_amount
            ret = Post_order_place(
                access_key=self.access_key,
                secret_key=self.secret_key,
                account_id=self.account_id,
                symbol=self.symbol,
                type_value="sell-limit",
                amount=amount,
                price=price_in_sell_limit
            )
            if ret["status"] != "ok":
                self.log_print(" ret_status: %s  \n ret: %s "
                               % (ret["status"], ret))
                raise Exception("Failed tp Post_order_place in place_sell_limit")
            assert ret["status"] == "ok"
            sell_limit_order = {
                "price": price_in_sell_limit,
                "amount": amount,
                "finish": False
            }
            self.sell_limit_order_list.append(sell_limit_order)
            self.show_current_profit_and_loss(cur_status="place_sell_limit")
            return True
        except Exception as ex:
            self.log_print("Exception in place_sell_limit!")
            self.log_print("ex: %s" % ex)
            return False

    # 处理成交的限价卖单
    def dispose_sell_limit_orders(self, pre_1_k_line_data):
        last_high_price = pre_1_k_line_data["high_price"]
        b_show = False
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
        self.log_print("当前持有的 quoter 的数量: %s" % self.holding_quoter_amount)
        self.log_print("当前累计的 quoter 收益: %s" % self.quoter_accumulated_income)
        count = 0
        for item in self.sell_limit_order_list:
            if not item["finish"]:
                count += 1
        self.log_print("当前限价卖单的挂单量: %s" % count)
        self.log_print("已经成交的限价卖单的挂单量: %s" % (len(self.sell_limit_order_list) - count))
        if self.quoter_total_cost != 0.0:
            income_rate = float(self.quoter_accumulated_income) / float(self.quoter_total_cost)
            self.log_print("当前的收益率: %s%%" % (income_rate * 100.0))
            if delta_time != 0.0:
                already_run_days = delta_time / (24*60*60)
                income_rate_by_day = income_rate / already_run_days
                self.log_print("日均收益率: %s%%" % (income_rate_by_day * 100.0))
        self.log_print("\n################## %s ##################\n" % cur_status)
        return True

    # 获取近3次的K线数据
    def get_3_kline_data(self, symbol, period="5min"):
        self.wait_to_next_X_min_begin(x=get_period_int(period))
        ret_data = self.get_kline_data(
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

    def get_3_kline_data_2(self,symbol="ethusdt", period="5min"):
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
                    # 模拟下限价卖单
                    self.simulate_place_sell_limit(k_line_data=cur_k_line_data)
        except Exception as ex:
            self.log_print("Exception in do_strategy_execute")
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
            while not run_time_config_data["quit"]:
                if run_time_config_data["keep_run"]:
                    k_line_data_list = self.get_3_kline_data(symbol=symbol, period=period)
                    # 处理成交的限价卖单
                    self.dispose_sell_limit_orders(pre_1_k_line_data=k_line_data_list[1])
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
                        # 买入Base
                        OK = self.buy_base(k_line_data=cur_k_line_data)
                        if not OK:
                            continue
                        # 下限价卖单
                        self.place_sell_limit()
                else:
                    time.sleep(2)
                run_time_config_data = self.get_run_time_configuration()
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
    print("投入的总成本: %s" % my_strategy.quoter_total_cost)
    print("当前持有的 quoter 的数量: %s" % my_strategy.holding_quoter_amount)
    print("当前累计的 quoter 收益: %s" % my_strategy.quoter_accumulated_income)
    count = 0
    for item in my_strategy.sell_limit_order_list:
        if not item["finish"]:
            count += 1
    print("当前限价卖单的挂单量: %s" % count)
    print("已经成交的限价卖单的挂单量: %s" % (len(my_strategy.sell_limit_order_list) - count))
    income_rate = float(my_strategy.quoter_accumulated_income) / float(my_strategy.quoter_total_cost)
    print("当前的收益率: %s%%" % (income_rate * 100.0))
    income_rate_by_day = income_rate / run_days
    print("日均收益率: %s%%" % (income_rate_by_day * 100.0))
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
        {"symbol": "ethusdt", "increasing_price_rate": 0.02},
        {"symbol": "ethusdt", "increasing_price_rate": 0.04},
        {"symbol": "ethusdt", "increasing_price_rate": 0.08},
        #{"symbol": "dotusdt", "increasing_price_rate": 0.01},
        #{"symbol": "linkusdt", "increasing_price_rate": 0.01},
        #{"symbol": "ltcusdt", "increasing_price_rate": 0.01},
    ]
    total_quoter_total_cost = 0.0
    total_quoter_accumulated_income = 0.0
    total_income_rate = 0.0
    total_income_rate_by_day = 0.0
    # period = "5min"
    # period = "15min"
    # period = "30min"
    # period = "60min"
    period = "4hour"
    size = int(6*24*60/240)
    buy_min_quoter_amount = 6.0 * 12 * 4
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
    print(Show_delta_time(delta_time=(1*24*60*60+5*60*60+27*60+16)))
    # delta_time = 1*24*60*60+5*60*60+27*60+16
    # already_run_days = delta_time / (24 * 60 * 60)
    # print("已经运行 %s 天" % already_run_days)
    # print(TimeStamp_to_datetime(time.time()))
    # ret = Get_market_depth(
    #     symbol="ethusdt"
    # )
    # first_buy_price = ret["tick"]["bids"][0][0]
    # print(first_buy_price)
    # first_sell_price = ret["tick"]["asks"][0][0]
    # print(first_sell_price)

    # bench_earn_money()

    # bSuccessToBuy = False
    # count = 0
    # while not bSuccessToBuy and count < 5:
    #     count += 1
    #     bSuccessToBuy = try_buy_coins()
    #     if bSuccessToBuy:
    #         print("Success to BUY !")
    #         break
    #     else:
    #         time.sleep(1)
    #         print("Fail to BUY ! retry %s" % count)

    # symbol = "btcusdt"
    # period = "5min"
    # run_days = 2
    # increasing_price_rate = 0.01
    # buy_min_quoter_amount = 6.0
    # time_stamp = int(time.time())
    # dt_stamp = TimeStamp_to_datetime(time_stamp)
    # my_strategy = Strategy_01()
    # my_strategy.init_all()
    # my_strategy.increasing_price_rate = increasing_price_rate
    # my_strategy.do_strategy_execute(
    #     symbol=symbol,
    #     period=period,
    #     run_days=run_days,
    #     buy_min_quoter_amount=buy_min_quoter_amount,
    #     dt_stamp=dt_stamp
    # )