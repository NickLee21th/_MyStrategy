from decimal import *
import math
import datetime
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
import logging
import time
import multiprocessing
from multiprocessing import Pool, Manager
from project.demos.Strategy_Base import *


class Strategy_01(Strategy_Base):
    holding_base_amount = 0.0  # 当前持有的 Base 的数量
    cur_buy_base_amount = 0.0  # 最近一次购入的 Base 的数量
    quoter_total_cost = 0.0  # 投入的总成本(quoter)
    holding_quoter_amount = 5000.0  # 当前持有的 quoter 的数量
    quoter_accumulated_income = 0.0  # 当前累计的 quoter 收益
    increasing_price_rate = 0.01  # 下限价卖单时的价格增加率
    sell_limit_order_list = []  # 当前未成交的限价卖单列表

    test_k_line_data_list = []
    test_k_line_data_index = 999  # 1999

    def init_all(self):
        self.holding_base_amount = 0.0  # 当前持有的 Base 的数量
        self.cur_buy_base_amount = 0.0  # 最近一次购入的 Base 的数量
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

    # 买入Base
    def buy_base(self, k_line_data):
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
            self.log_print("Exception in buy_base!")
            self.log_print("ex: %s" % ex)
            return False

    # 下限价卖单
    def place_sell_limit(self, k_line_data):
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
            self.log_print("Exception in place_sell_limit!")
            self.log_print("ex: %s" % ex)
            return False

    # 处理成交的限价卖单
    def dispose_sell_limit_orders(self, pre_1_k_line_data):
        last_high_price = pre_1_k_line_data["high_price"]
        for sell_limit_order in self.sell_limit_order_list:
            if not sell_limit_order["finish"] and sell_limit_order["price"] < last_high_price:  # 限价卖单已经成交
                cur_quoter_income = float(sell_limit_order["amount"]) * float(sell_limit_order["price"])
                # 当前持有的 Base 的数量 减少
                self.holding_base_amount += self.cur_buy_base_amount
                # 投入的总成本(quoter) 减少
                self.quoter_total_cost -= self.buy_min_quoter_amount
                # 当前持有的 quoter 的数量 增加
                self.holding_quoter_amount += cur_quoter_income
                # 当前累计的 quoter 收益 增加
                self.quoter_accumulated_income += (cur_quoter_income - self.buy_min_quoter_amount)
                # 标记限价卖单已成交
                sell_limit_order["finish"] = True
        return True

    def get_3_kline_data(self, symbol, period="5min"):
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

    def do_strategy_execute(self, symbol, period, buy_min_quoter_amount, dt_stamp):
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
                    self.buy_base(k_line_data=cur_k_line_data)
                    # 下限价卖单
                    self.place_sell_limit(k_line_data=cur_k_line_data)
        except Exception as ex:
            self.log_print("Exception in do_strategy_execute")
            self.log_print("ex: %s" % ex)

def get_period_int(period):
    period_int = 5
    if period == "5min":
        period_int = 5
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
    my_strategy.do_strategy_execute(
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


if __name__ == '__main__':
    symbol_list = [
        "ethusdt",
        "btcusdt",
        "dotusdt",
        "linkusdt",
        "ltcusdt",
    ]
    total_quoter_total_cost = 0.0
    total_quoter_accumulated_income = 0.0
    total_income_rate = 0.0
    total_income_rate_by_day = 0.0
    period = "5min"
    size = 2000
    buy_min_quoter_amount = 5.0
    increasing_price_rate = 0.01  # 下限价卖单时的价格增加率
    for symbol in symbol_list:
        (
            quoter_total_cost,
            quoter_accumulated_income,
            income_rate,
            income_rate_by_day
        ) = earn_method(
            symbol=symbol,
            period=period,
            size=size,
            buy_min_quoter_amount=buy_min_quoter_amount,
            increasing_price_rate=increasing_price_rate
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