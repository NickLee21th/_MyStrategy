from decimal import *
import math
import datetime
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
import logging
import time
import multiprocessing
from multiprocessing import Pool, Manager

TIME_PERIOD = "5min"  # 1min, 5min, 15min, 30min
TIME_PERIOD_VALUE = 5
STOP_LOST_RATE = -0.5  # 止损

class DemoStrategy:
    BASE_INVEST = 20
    current_balance = BASE_INVEST / 2
    once_invest = BASE_INVEST / 2
    last_symbol = "Nothing"
    last_currency = "Nothing"
    last_amount = 0.0
    earning_ratio = 0.0
    stop_actual_invest = False
    actual_balance = current_balance
    actual_last_symbol = "Nothing"
    actual_last_currency = "Nothing"
    actual_last_amount = 0.0
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    s_access_key = S_ACCESS_KEY
    s_secret_key = S_SECRET_KEY
    etp = ""
    history_size = 1000  # 20  # 300
    threshold_value_adjust_rate = 0.0
    dt_stamp = ""
    demo_logger = None
    data_dict = {}
    queue = None
    demo_action_launch_time = int(time.time())

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
                    log_folder_name="demo_log",
                    log_file_template="/demo_%s_%s.log"
                    ):
        logger = logging.getLogger(self.etp)
        logger.setLevel(level=logging.INFO)
        dt_value = self.dt_stamp
        log_file_name = log_file_template % (dt_value, self.etp)
        handler = logging.FileHandler(log_folder_name+log_file_name)
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

    def plan_A(self,
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
            self.demo_print("Exception in plan_A")
            self.demo_print("symbol_base=%s, start=%s, end=%s, "
                            "len(trend_base_list)=%s, len(trend_3l_list)=%s, len(trend_3s_list)=%s"
                            % (symbol_base, start, end, len(trend_base_list), len(trend_3l_list), len(trend_3s_list)))
            self.demo_print(ex)
        # hbgAnyCall.log_print("%s .... earn_value = %s" % (symbol_base, earn_value))
        # hbgAnyCall.log_print("%s .... no_change_count = %s" % (symbol_base, no_change_count))
        return earn_value

    def plan_B(self,
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
            self.demo_print("Exception in plan_B")
            self.demo_print("symbol_base=%s, start=%s, end=%s, "
                            "len(trend_base_list)=%s, len(trend_3l_list)=%s, len(trend_3s_list)=%s"
                            % (symbol_base, start, end, len(trend_base_list), len(trend_3l_list), len(trend_3s_list)))
            self.demo_print(ex)
        # hbgAnyCall.log_print("%s .... earn_value = %s" % (symbol_base, earn_value))
        # hbgAnyCall.log_print("%s .... no_change_count = %s" % (symbol_base, no_change_count))
        return earn_value

    # 市价买入指定币种
    def buy_market(self, symbol="", amount=10.0):
        if symbol == "":
            return False, None
        ret = False
        retry_count = 0
        response = None
        while ret is False and retry_count < 30:
            try:
                response = Post_order_place(
                    access_key=self.s_access_key,
                    secret_key=self.s_secret_key,
                    account_id=self.account_id,
                    symbol=symbol,
                    type_value="buy-market",
                    amount=amount,
                )
                if response is not None:
                    status = response["status"]
                    if status == "ok":
                        ret = True
                        break
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
            except Exception as ex:
                self.demo_print("Exception in buy_market")
                self.demo_print("symbol = %s , ex = %s" % (symbol, ex))
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return ret, response

    # 限价卖出指定币种
    def sell_limit_price(self, symbol="", amount=0.0, limit_price=0.0):
        if symbol == "" or amount <= 0.0 or limit_price <=0.0:
            return False, None
        n_bits = Get_orderamount_precision(symbol)
        amount = decimals_accuracy_n(
            inputDecimals=amount,
            n_bits=n_bits,
            accuracy_type='trunc'
        )
        self.demo_print("### in sell_limit_price, symbol: %s, amount: %s, limit_price: %s"
                        % (symbol, amount, limit_price))
        ret = False
        retry_count = 0
        response = None
        while ret is False and retry_count < 30:
            try:
                response = Post_order_place(
                    access_key=self.s_access_key,
                    secret_key=self.s_secret_key,
                    account_id=self.account_id,
                    symbol=symbol,
                    type_value="sell-limit",
                    amount=amount,
                    price=limit_price,
                )
                if response is not None:
                    status = response["status"]
                    if status == "ok":
                        ret = True
                        break
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
            except Exception as ex:
                self.demo_print("Exception in sell_limit_price")
                self.demo_print("SELL symbol = %s, amount = %s, ex = %s"
                                % (symbol, amount, ex))
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return ret, response

    # 数量值截断
    def truncate_amount(self, symbol, amount):
        n_bits = Get_orderamount_precision(symbol)
        amount = decimals_accuracy_n(
            inputDecimals=amount,
            n_bits=n_bits,
            accuracy_type='trunc'
        )
        return amount

    # 市价卖出指定币种
    def sell_market(self, symbol="", amount=0):
        if symbol == "" or amount <= 0:
            return False, None
        amount = self.truncate_amount(symbol, amount)
        ret = False
        retry_count = 0
        response = None
        while ret is False and retry_count < 30:
            try:
                response = Post_order_place(
                    access_key=self.s_access_key,
                    secret_key=self.s_secret_key,
                    account_id=self.account_id,
                    symbol=symbol,
                    type_value="sell-market",
                    amount=amount,
                )
                if response is not None:
                    status = response["status"]
                    if status == "ok":
                        ret = True
                        break
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
            except Exception as ex:
                self.demo_print("Exception in sell_market")
                self.demo_print("SELL symbol = %s, amount = %s, ex = %s"
                                % (symbol, amount, ex))
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return ret, response

    # 获取指定币种的当前可用余额
    def get_currency_balance(
            self,
            access_key, secret_key,
            account_id,
            currency,  # 币种名称
            type_value  # trade: 交易余额，frozen: 冻结余额, loan: 待还借贷本金,
            # interest: 待还借贷利息, lock: 锁仓, bank: 储蓄
    ):
        balance_value = "-1"
        ret = False
        retry_count = 0
        while ret is False and retry_count < 10:
            try:
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
                            self.demo_print("Failed to get the balance, currency=%s, type_value=%s"
                                            % (currency, type_value))
                            ret = False
                            retry_count += 1
                            time.sleep(2)
                            continue
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
            except Exception as ex:
                self.demo_print("Exception in get_currency_balance")
                self.demo_print("currency=%s, type_value=%s, ex = %s"
                                % (currency, type_value, ex))
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return ret, balance_value

    # 行动
    def demon_action(self, log_folder_name="demo_action_log"):
        self.logger_init(log_folder_name=log_folder_name, log_file_template="/action_%s_%s.txt")
        self.demo_print("I'm %s in demo_action" % self.etp)
        wait_to_X_min_begin(x=TIME_PERIOD_VALUE)
        self.demo_action_launch_time = int(time.time())
        count = 0
        Max_Count = 1000*5
        while count < Max_Count:
            time_stamp_start = int(time.time())
            self.data_dict = {}
            self.do_action(count)
            time_stamp_end = int(time.time())
            sleep_time = 60 * TIME_PERIOD_VALUE - (time_stamp_end - time_stamp_start)
            if sleep_time > 0:
                print("time_stamp_start = %s   time_stamp_end = %s " %
                      (timeStamp_to_datetime(time_stamp_start), timeStamp_to_datetime(time_stamp_end)))
                self.demo_print("sleep %s seconds ....." % sleep_time)
                time.sleep(sleep_time)
            else:
                print("Waiting time more than %s minutes! "  % TIME_PERIOD_VALUE)
                print("time_stamp_start = %s   time_stamp_end = %s " %
                      (timeStamp_to_datetime(time_stamp_start), timeStamp_to_datetime(time_stamp_end)))
            count += 1
            if self.earning_ratio < STOP_LOST_RATE:  # 触发止损
                self.demo_print("***** ACCESS STOP_LOST_RATE and STOP to RUN!! *****")
                self.demo_print("***** earning_ratio = %s *****" % self.earning_ratio)
                break

    def get_duration(self, seconds, format="%d:%02d:%02d"):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    # 卖出上一次持有的杠杆代币
    def sell_last_hold_lever_coins(self, action_index):
        if self.last_symbol != "Nothing":
            ts_sell, sell_cur_price = get_current_price(symbol=self.last_symbol, )
            ts_sell = int(ts_sell / 1000)
            self.demo_print("SELL LAST COIN")
            running_duration = self.get_duration(ts_sell - self.demo_action_launch_time)
            self.demo_print("last_symbol:%s, last_currency:%s, last_amount:%s, sell_cur_price:%s" %
                            (self.last_symbol, self.last_currency, self.last_amount, sell_cur_price))
            amount = self.truncate_amount(self.last_symbol, self.last_amount)
            last_sell_cash = sell_cur_price * amount
            self.demo_print("sell_cur_price * last_amount = %s" % last_sell_cash)
            self.current_balance += last_sell_cash
            self.demo_print("current_balance = %s  sell_ts:%s  demo_action_launch_time: %s"
                            % (self.current_balance, timeStamp_to_datetime(ts_sell),
                               timeStamp_to_datetime(self.demo_action_launch_time)))
            self.earning_ratio = (self.current_balance - self.once_invest) / self.once_invest
            self.demo_print("demo_action_running_duration: %s" % running_duration)
            self.demo_print("earning_ratio = %s%%" % (self.earning_ratio * 100.0))
            self.last_symbol = "Nothing"
            self.last_currency = "Nothing"
            self.last_amount = 0.0
            # Actual sell
            if self.actual_last_symbol != "Nothing":
                self.demo_print("***** ACTUAL SELL LAST COIN *****")
                # fake call
                # ts_actual_sell, actual_sell_cur_price = get_current_price(symbol=self.actual_last_symbol, )
                # ts_actual_sell = int(ts_actual_sell / 1000)
                # self.demo_print("actual_last_symbol:%s, actual_last_currency:%s, actual_last_amount:%s, actual_sell_cur_price:%s" %
                #                 (self.actual_last_symbol, self.actual_last_currency, self.actual_last_amount, actual_sell_cur_price))
                # self.demo_print("actual_sell_cur_price * actual_last_amount = %s" % (actual_sell_cur_price * self.actual_last_amount))
                # self.actual_balance += actual_sell_cur_price * self.actual_last_amount
                # self.demo_print("actual_balance=%s, ts_actual_sell=%s"
                #                 % (self.actual_balance, timeStamp_to_datetime(ts_actual_sell)))
                # self.actual_last_symbol = "Nothing"
                # self.actual_last_currency = "Nothing"
                # self.actual_last_amount = 0.0

                # real call
                # ret, actual_sell_market_cash = self.actual_sell_market_level_coins(
                #     symbol=self.actual_last_symbol,
                #     amount=self.actual_last_amount
                # )
                ret, actual_sell_market_cash = self.actual_sell_limit_price_level_coins(
                    symbol=self.actual_last_symbol,
                    amount=self.actual_last_amount,
                    limit_price=sell_cur_price
                )
                if ret is True:
                    self.demo_print("actual_last_symbol:%s, actual_last_currency:%s, actual_last_amount:%s, actual_sell_market_cash:%s" %
                                    (self.actual_last_symbol, self.actual_last_currency, self.actual_last_amount, actual_sell_market_cash))
                    self.demo_print("actual_balance=%s, ts_actual_sell=%s"
                                    % (self.actual_balance, timeStamp_to_datetime(int(time.time()))))
            self.demo_print("***** KEEP  stop_actual_invest = False  *****")
            self.stop_actual_invest = False
            if self.earning_ratio < STOP_LOST_RATE:  # 触发止损
                self.demo_print("***** SET  stop_actual_invest = True  *****")
                self.demo_print("***** earning_ratio = %s *****" % self.earning_ratio)
                self.stop_actual_invest = True
            # update stop_actual_invest
            # self.demo_print("***** update stop_actual_invest  *****")
            # self.demo_print("last_sell_cash=%s" % last_sell_cash)
            # if self.earning_ratio < STOP_LOST_RATE:  # 触发止损
            #     self.stop_actual_invest = True
            # else:
            #     if last_sell_cash < self.once_invest:  # 触发止损
            #         self.stop_actual_invest = True
            #     else:
            #         self.stop_actual_invest = False

            # queue_info
            queue_info = {
                'action_index': self.get_duration(action_index * TIME_PERIOD_VALUE*60),
                'do_action': True,
                'ts': timeStamp_to_datetime(int(time.time())),
                'symbol': self.etp + "usdt",
                'earning_ratio': self.earning_ratio,
                'current_balance': self.current_balance,
                'actual_balance': self.actual_balance,
                'stop_actual_invest': self.stop_actual_invest,
                'demo_action_running_duration': running_duration,
            }
        else:
            if self.actual_last_symbol != "Nothing":
                self.demo_print("ERROR!! actual_last_symbol SHOULD BE Nothing!")
                self.demo_print("actual_last_symbol = %s" % self.actual_last_symbol)
                assert self.actual_last_symbol == "Nothing"
            cur_time = int(time.time())
            running_duration = self.get_duration(cur_time - self.demo_action_launch_time)
            queue_info = {
                'action_index': self.get_duration(action_index * TIME_PERIOD_VALUE*60),
                'do_action': False,
                'ts': timeStamp_to_datetime(cur_time),
                'symbol': self.etp + "usdt",
                'earning_ratio': self.earning_ratio,
                'current_balance': self.current_balance,
                'actual_balance': self.actual_balance,
                'stop_actual_invest': self.stop_actual_invest,
                'demo_action_running_duration': running_duration,
            }
        self.demo_print("SEND QUEUE INFO - START")
        if self.queue.full():
            self.demo_print("THE QUEUE IS FULL!")
        else:
            self.queue.put(queue_info)
            self.demo_print("SEND QUEUE INFO - FINISH")

    # 市价买入新的杠杆代币
    def buy_lever_coins(self, symbol, currency, cur_price, ts):
        self.demo_print("current_balance = %s" % self.current_balance)
        self.demo_print("BUY NEW COINS")
        self.demo_print("symbol:%s, currency:%s, cur_price:%s, amount=%s, ts:%s"
                        % (symbol, currency, cur_price, (self.once_invest / cur_price),
                           timeStamp_to_datetime(int(ts/1000))))
        self.current_balance -= self.once_invest
        if self.stop_actual_invest is False:
            self.demo_print("ACTUAL - BUY NEW COINS")
            # fake CALL
            # self.actual_balance -= self.once_invest
            # self.actual_last_symbol = symbol
            # self.actual_last_currency = currency
            # self.actual_last_amount = self.once_invest / cur_price

            # real Call
            self.actual_buy_market_level_coins(symbol, currency)

        self.last_symbol = symbol
        self.last_currency = currency
        self.last_amount = self.once_invest / cur_price

    def get_actual_buy_market_amount(self, order_id=""):
        if order_id == "":
            return -1
        actual_buy_market_amount = -1
        ret = False
        retry_count = 0
        while ret is False and retry_count < 30:
            try:
                response = Get_orders_details(
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    order_id=order_id,
                )
                if response is not None:
                    status = response["status"]
                    if status == "ok":
                        data = response["data"]
                        state = data["state"]
                        if state != "filled":
                            ret = False
                            retry_count += 1
                            time.sleep(2)
                            continue
                        else:
                            ret = True
                            field_amount = float(data["field-amount"])
                            # field_fees = float(data["field-fees"])
                            price = float(data["price"])
                            actual_buy_market_amount = field_amount  # - field_fees
                            self.demo_print("IN get_actual_buy_market_amount")
                            self.demo_print("order_id=%s, field_amount=%s, price=%s, actual_buy_market_amount=%s"
                                            % (order_id, field_amount, price, actual_buy_market_amount))
                            break
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
            except Exception as ex:
                self.demo_print("Exception in get_actual_buy_market_amount")
                self.demo_print("order_id = %s" % order_id)
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return ret, actual_buy_market_amount

    def actual_buy_market_level_coins(self, symbol, currency):
        self.demo_print("**** DO BUY actual_buy_market_level_coins  ******** ")
        amount = self.once_invest
        ret, response = self.buy_market(symbol, amount)
        if ret is True:
            actual_buy_market_amount = -1
            try:
                order_id = response["data"]
                ret, actual_buy_market_amount = self.get_actual_buy_market_amount(order_id)
            except Exception as ex:
                self.demo_print("Exception in get actual buy market amount! ")
            if ret is True and float(actual_buy_market_amount) > 0.0:
                self.actual_balance -= self.once_invest
                self.actual_last_symbol = symbol
                self.actual_last_currency = currency
                self.actual_last_amount = float(actual_buy_market_amount)
                self.demo_print("actual_last_symbol=%s actual_last_amount=%s"
                                % (self.actual_last_symbol, self.actual_last_amount))
        else:
            self.demo_print("FAILED to BUY NEW COINS indeed!")
            self.demo_print("symbol=%s, ts=%s" % (symbol, timeStamp_to_datetime(int(time.time()))))
            if response is not None:
                self.demo_print("response = %s" % response)
        return ret

    def get_actual_sell_market_cash(self, order_id=""):
        if order_id == "":
            return -1
        actual_sell_market_cash = -1
        ret = False
        retry_count = 0
        while ret is False and retry_count < 30:
            try:
                response = Get_orders_details(
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    order_id=order_id,
                )
                if response is not None:
                    status = response["status"]
                    if status == "ok":
                        data = response["data"]
                        state = data["state"]
                        if state != "filled":
                            ret = False
                            retry_count += 1
                            time.sleep(2)
                            continue
                        else:
                            ret = True
                            field_cash_amount = float(data["field-cash-amount"])
                            # field_fees = float(data["field-fees"])
                            price = float(data["price"])
                            actual_sell_market_cash = field_cash_amount  # - field_fees
                            self.demo_print("IN get_actual_sell_market_cash")
                            self.demo_print("order_id=%s, field_cash_amount=%s, price=%s, actual_sell_market_cash=%s"
                                            % (order_id, field_cash_amount, price, actual_sell_market_cash))
                            break
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
            except Exception as ex:
                self.demo_print("Exception in get_actual_buy_market_amount")
                self.demo_print("order_id = %s" % order_id)
                ret = False
                retry_count += 1
                time.sleep(2)
                continue
        return ret, actual_sell_market_cash

    def actual_sell_limit_price_level_coins(self, symbol, amount, limit_price):
        self.demo_print("**** DO SELL actual_sell_limit_price_level_coins  ******** ")
        ret, response = self.sell_limit_price(symbol, amount, limit_price)
        actual_sell_market_cash = 0.0
        if ret is True:
            actual_sell_market_cash = limit_price * amount
            self.actual_balance += actual_sell_market_cash
            self.actual_last_symbol = "Nothing"
            self.actual_last_currency = "Nothing"
            self.actual_last_amount = 0.0
        else:
            self.demo_print("FAILED in  actual_sell_limit_price_level_coins!")
            self.demo_print("symbol=%s, ts=%s" % (symbol, timeStamp_to_datetime(int(time.time()))))
            if response is not None:
                self.demo_print("response = %s" % response)
        return ret, actual_sell_market_cash

    def actual_sell_market_level_coins(self, symbol, amount):
        self.demo_print("**** DO SELL actual_sell_market_level_coins  ******** ")
        ret, response = self.sell_market(symbol, amount)
        actual_sell_market_cash = 0.0
        if ret is True:
            actual_sell_market_cash = 0.0
            try:
                order_id = response["data"]
                ret, actual_sell_market_cash = self.get_actual_sell_market_cash(order_id)
            except Exception as ex:
                self.demo_print("Exception in get actual sell market amount! ")
                self.demo_print("symbol=%s  amount=%s  ex=%s" % (symbol, amount, ex))
                ret = False
            if ret is True:
                self.actual_balance += actual_sell_market_cash
                self.actual_last_symbol = "Nothing"
                self.actual_last_currency = "Nothing"
                self.actual_last_amount = 0.0
        else:
            self.demo_print("FAILED to SELL HOLD COINS indeed!")
            self.demo_print("symbol=%s, ts=%s" % (symbol, timeStamp_to_datetime(int(time.time()))))
            if response is not None:
                self.demo_print("response = %s" % response)
        return ret, actual_sell_market_cash

    # 行动器
    def do_action(self, action_index):
        try:
            self.demo_print("do_action -sell_last_hold_lever_coins StartTime= %s"
                            % timeStamp_to_datetime(int(time.time())))
            # 卖出上一次持有的代币
            self.sell_last_hold_lever_coins(action_index)
            self.demo_print("do_action -sell_last_hold_lever_coins FinishTime= %s"
                            % timeStamp_to_datetime(int(time.time())))
            period = TIME_PERIOD
            size = int(self.history_size)
            step_range = int(size / 2)
            cur_ts = 1000
            last_ts = 0
            trend_base_list = None
            trend_3l_list = None
            trend_3s_list = None
            self.demo_print("do_action -get_ALL_symbol_trend_data StartTime= %s"
                            % timeStamp_to_datetime(int(time.time())))
            while (cur_ts-last_ts) > (60*TIME_PERIOD_VALUE):
                trend_base_list, trend_3l_list, trend_3s_list \
                    = self.get_ALL_symbol_trend_data(
                    symbol_base=(self.etp + "usdt"),
                    symbol_l=(self.etp + "3lusdt"),
                    symbol_s=(self.etp + "3susdt"),
                    period=period,
                    size=size,
                )
                last_ts = trend_base_list[0]["dt"]
                # self.demo_print("last_ts = %s  %s " % (last_ts, timeStamp_to_datetime(last_ts)))
                cur_ts = int(time.time())
                # self.demo_print("cur_ts = %s  %s " % (cur_ts, timeStamp_to_datetime(cur_ts)))
            self.demo_print("do_action -get_ALL_symbol_trend_data FinishTime= %s" % timeStamp_to_datetime(int(time.time())))
            self.demo_print("do_action -judge_invest_direction StartTime= %s" % timeStamp_to_datetime(int(time.time())))
            last_ts, last_trend, invest_direction = self.judge_invest_direction(
                trend_base_list=trend_base_list,
                trend_3l_list=trend_3l_list,
                trend_3s_list=trend_3s_list,
                symbol_base=(self.etp + "usdt"),
                start_point=step_range-1,
                end_point=-1,
            )
            self.demo_print("do_action -judge_invest_direction FinishTime= %s" % timeStamp_to_datetime(int(time.time())))
            cur_ts = int(time.time())
            assert (60*TIME_PERIOD_VALUE) < (cur_ts-last_ts)
            # 根据 invest_direction 获取交易对价格
            self.demo_print("invest_direction=%s, last_trend=%s, last_ts=%s"
                            % (invest_direction, last_trend, timeStamp_to_datetime(last_ts)))
            symbol_l = self.etp + "3lusdt"
            currency_l = self.etp + "3l"
            cur_price_l = 0.0
            ts_l = 1
            symbol_s = self.etp + "3susdt"
            currency_s = self.etp + "3s"
            cur_price_s = 0.0
            ts_s = 1
            self.demo_print("do_action -buy_lever_coins StartTime= %s"
                            % timeStamp_to_datetime(int(time.time())))
            if invest_direction == "planA":  # 顺势
                if last_trend == 1:  # 涨
                    ts_l, cur_price_l = get_current_price(symbol=symbol_l)
                    # 市价买入新的杠杆代币
                    self.buy_lever_coins(symbol=symbol_l, currency=currency_l, cur_price=cur_price_l, ts=ts_l)
                elif last_trend == -1:  # 跌
                    ts_s, cur_price_s = get_current_price(symbol=symbol_s)
                    # 市价买入新的杠杆代币
                    self.buy_lever_coins(symbol=symbol_s, currency=currency_s, cur_price=cur_price_s, ts=ts_s)
            elif invest_direction == "planB":  # 逆势
                if last_trend == 1:  # 涨
                    ts_s, cur_price_s = get_current_price(symbol=symbol_s)
                    # 市价买入新的杠杆代币
                    self.buy_lever_coins(symbol=symbol_s, currency=currency_s, cur_price=cur_price_s, ts=ts_s)
                elif last_trend == -1:  # 跌
                    ts_l, cur_price_l = get_current_price(symbol=symbol_l)
                    # 市价买入新的杠杆代币
                    self.buy_lever_coins(symbol=symbol_l, currency=currency_l, cur_price=cur_price_l, ts=ts_l)
            else:  # invest_direction == "no_plan"
                # 卖出上一次持有的代币
                print("  ")
                # self.sell_last_hold_lever_coins(action_index)
            self.demo_print("do_action -buy_lever_coins FinishTime= %s"
                            % timeStamp_to_datetime(int(time.time())))
            self.demo_print("=========================================")
        except Exception as ex:
            self.demo_print("Exception in do_action")
            self.demo_print("ex = %s" % ex)

    # 预言机
    def demon_prediction(self):
        self.logger_init()
        self.demo_print("I'm %s" % self.etp)
        try:
            period = "5min"  # 1min, 5min, 15min, 30min
            size = 1000  # 2000
            step_range = int(size / 4)
            trend_base_list, trend_3l_list, trend_3s_list \
                = self.get_ALL_symbol_trend_data(
                symbol_base=(self.etp + "usdt"),
                symbol_l=(self.etp + "3lusdt"),
                symbol_s=(self.etp + "3susdt"),
                period=period,
                size=size,
            )
            self.demo_print("%s  judge_invest_direction START" % self.etp)
            invest_direction_list = []
            for i in range(int(size / 2) - 1, -1, -1):
                # print("%s -step 1-%s" % (self.etp, i))
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
            self.demo_print("%s  judge_invest_direction FINISH" % self.etp)
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
        self.demo_print("%s  get_ALL_symbol_trend_data START" % self.etp)
        self.demo_print("StartTime= %s" % timeStamp_to_datetime(int(time.time())))
        # base
        symbol = symbol_base
        trend_base_list = self.get_symbol_trend_data(
            symbol=symbol,
            period=period, size=size
        )
        assert trend_base_list
        self.demo_print("%s  %s" % (symbol_base, len(trend_base_list)))
        assert size == len(trend_base_list)
        # 3l
        symbol = symbol_l
        trend_3l_list = self.get_symbol_trend_data(
            symbol=symbol,
            period=period, size=size
        )
        assert trend_3l_list
        self.demo_print("%s  %s" % (symbol_l, len(trend_3l_list)))
        assert size == len(trend_3l_list)
        # 3s
        symbol = symbol_s
        trend_3s_list = self.get_symbol_trend_data(
            symbol=symbol,
            period=period, size=size
        )
        assert trend_3s_list
        self.demo_print("%s  %s" % (symbol_s, len(trend_3s_list)))
        assert size == len(trend_3s_list)
        self.demo_print("%s  get_ALL_symbol_trend_data FINISH" % self.etp)
        self.demo_print("FinishTime= %s" % timeStamp_to_datetime(int(time.time())))
        return trend_base_list, trend_3l_list, trend_3s_list

    # 获取交易对的K线信息，整理后返回。
    def get_symbol_trend_data(self, symbol, period, size):
        trend_symbol_list = []
        try:
            k_line_res = None
            ret = False
            retry_count = 0
            while ret is False and retry_count < 30:
                k_line_res = Get_kline_data(
                    symbol=symbol,
                    period=period, size=size
                )
                if k_line_res is None or k_line_res["status"] != "ok":
                    if k_line_res is not None:
                        self.demo_print(k_line_res)
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
                    if delta < (60*TIME_PERIOD_VALUE):
                        finished = False
                    trend_symbol_item = {
                        "dt": item["id"],
                        "symbol": symbol,
                        "open": item["open"],
                        "close": item["close"],
                        "finished": finished
                    }
                    trend = 0  # 平
                    close_price = float(item["close"])
                    open_price = float(item["open"])
                    if close_price < open_price:
                        trend = -1  # 跌
                    elif close_price > open_price:
                        trend = 1  # 涨
                    change_rate = (close_price - open_price) / open_price
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
        last_open = trend_base_list[index]["open"]
        last_close = trend_base_list[index]["close"]
        last_ts = trend_base_list[index]["dt"]
        invest_direction = "no_plan"
        if count_B_earn > 0 and count_B_earn > count_A_earn \
                and count_B_earn > (step_range * self.threshold_value_adjust_rate):
            invest_direction = "planB"
        elif count_A_earn > 0 and count_A_earn > count_B_earn \
                and count_A_earn > (step_range * self.threshold_value_adjust_rate):
            invest_direction = "planA"
        self.demo_print("count_A_earn = %s , count_B_earn = %s , threshold_value=%s"
                        % (count_A_earn, count_B_earn, step_range*self.threshold_value_adjust_rate))
        self.demo_print("last_open=%s, last_close=%s, invest_direction=%s, last_ts=%s"
                        % (last_open, last_close, invest_direction, timeStamp_to_datetime(last_ts)))
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
                        = self.plan_A(symbol_base, index_i + step_range, index_i,
                                 trend_base_list, trend_3l_list, trend_3s_list)
                    earn_value_B \
                        = self.plan_B(symbol_base, index_i + step_range, index_i,
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

    # 输出 MD5 和 MD10
    def output_MA5_MA10(self, symbol="ethusdt", base="eth"):
        logger = logging.getLogger("Ma5Ma10")
        logger.setLevel(level=logging.INFO)
        time_stamp = int(time.time())
        dt_stamp = timeStamp_to_datetime(time_stamp)
        dt_value = dt_stamp
        log_file_name = "Ma5Ma10_%s_%s.txt" % (dt_value, symbol)
        handler = logging.FileHandler(log_file_name)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.demo_logger = logger
        # to_buy_3l = False
        # to_sell_3l = False
        # to_buy_3s = False
        # to_sell_3s = False
        last_delta = None
        up_trend = False
        down_trend = False
        symbol_3l = base + "3lusdt"
        symbol_3s = base + "3susdt"
        up_cross_3l_price = 0.0
        down_cross_3s_price = 0.0
        count = 0
        total_up_rate = 0.0
        total_down_rate = 0.0
        total_rate = 0.0
        lanuch_time = int(time.time())
        self.demo_print("symbol = %s, base = %s " % (symbol, base))
        self.demo_print("Launch Time = %s" % timeStamp_to_datetime(lanuch_time))
        while count < (1000*50):
            self.demo_print("================================================")
            count += 1
            try:
                ma5, ma10 = get_MA5_MA10(symbol)
                self.demo_print("Time = %s" % timeStamp_to_datetime(int(time.time())))
                self.demo_print(" MA5 = %s" % ma5)
                self.demo_print("MA10 = %s" % ma10)
                if ma5 > ma10 and last_delta is not None:
                    if last_delta <= 0.0:
                        self.demo_print("CATCH Up cross")
                        last_delta = ma5 - ma10
                        self.demo_print("last_delta = %s" % last_delta)
                        # 出现上涨信号，开始获取 3L 的价格
                        up_trend = True
                        down_trend = False
                        # 输出 3L 的价格
                        _, up_cross_3l_price = get_current_price(symbol_3l)
                        self.demo_print("Up Cross: %s = %s" % (symbol_3l, up_cross_3l_price))
                        # 输出 3S 的价格
                        _, cur_3s_price = get_current_price(symbol_3s)
                        self.demo_print("%s = %s" % (symbol_3s, cur_3s_price))
                        # 输出 down_rate
                        if down_cross_3s_price > 0.0:
                            down_rate = (cur_3s_price - down_cross_3s_price) / down_cross_3s_price
                            self.demo_print("down_rate = %s" % down_rate)
                            total_down_rate += down_rate
                            self.demo_print("total_down_rate = %s" % total_down_rate)
                            total_rate = total_down_rate + total_up_rate
                            self.demo_print("total_rate = %s" % total_rate)
                    else:
                        last_delta = ma5 - ma10
                        if up_trend:
                            self.demo_print("IN Up Trend")
                            self.demo_print("last_delta = %s" % last_delta)
                            _, cur_3l_price = get_current_price(symbol_3l)
                            self.demo_print("%s = %s" % (symbol_3l, cur_3l_price))
                            self.demo_print("up_cross %s = %s" % (symbol_3l, up_cross_3l_price))
                            assert up_cross_3l_price > 0.0
                            up_rate = (cur_3l_price - up_cross_3l_price) / up_cross_3l_price
                            self.demo_print("up_rate = %s" % up_rate)
                elif ma5 < ma10 and last_delta is not None:
                    if last_delta >= 0.0:
                        self.demo_print("CATCH Down cross")
                        last_delta = ma5 - ma10
                        self.demo_print("last_delta = %s" % last_delta)
                        # 出现下跌信号，开始获取 3S 的价格
                        up_trend = False
                        down_trend = True
                        # 输出 3S 的价格
                        _, down_cross_3s_price = get_current_price(symbol_3s)
                        self.demo_print("Down Cross: %s = %s" % (symbol_3s, down_cross_3s_price))
                        # 输出 3L 的价格
                        _, cur_3l_price = get_current_price(symbol_3l)
                        self.demo_print("%s = %s" % (symbol_3l, cur_3l_price))
                        # 输出 up_rate
                        if up_cross_3l_price > 0.0:
                            up_rate = (cur_3l_price - up_cross_3l_price) / up_cross_3l_price
                            self.demo_print("up_rate = %s" % up_rate)
                            total_up_rate += up_rate
                            self.demo_print("total_up_rate = %s" % total_up_rate)
                            total_rate = total_up_rate + total_down_rate
                            self.demo_print("total_rate = %s" % total_rate)
                    else:
                        last_delta = ma5 - ma10
                        if down_trend:
                            self.demo_print("IN Down Trend")
                            self.demo_print("last_delta = %s" % last_delta)
                            # 输出 3S 的价格
                            _, cur_3s_price = get_current_price(symbol_3s)
                            self.demo_print("%s = %s" % (symbol_3s, cur_3s_price))
                            self.demo_print("down_cross %s = %s" % (symbol_3s, down_cross_3s_price))
                            # 输出 down_rate
                            assert down_cross_3s_price > 0.0
                            down_rate = (cur_3s_price - down_cross_3s_price) / down_cross_3s_price
                            self.demo_print("down_rate = %s" % down_rate)
                elif last_delta is None:
                    last_delta = ma5 - ma10
                else:
                    assert False
            except Exception as ex:
                self.demo_print("Exception in output_MA5_MA10!")
                self.demo_print("EX: %s" % ex)


    # 输出 MD5 和 MD10, 做本币
    def output_MA5_MA10_base(self, symbol="ethusdt"):
        logger = logging.getLogger("Ma5Ma10")
        logger.setLevel(level=logging.INFO)
        time_stamp = int(time.time())
        dt_stamp = timeStamp_to_datetime(time_stamp)
        dt_value = dt_stamp
        log_file_name = "Ma5Ma10_base_%s_%s.txt" % (dt_value, symbol)
        handler = logging.FileHandler(log_file_name)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.demo_logger = logger
        # to_buy_3l = False
        # to_sell_3l = False
        # to_buy_3s = False
        # to_sell_3s = False
        last_delta = None
        up_trend = False
        down_trend = False
        up_cross_price = 0.0
        count = 0
        total_up_rate = 0.0
        total_down_rate = 0.0
        total_rate = 0.0
        lanuch_time = int(time.time())
        self.demo_print("symbol = %s" % symbol)
        self.demo_print("Launch Time = %s" % timeStamp_to_datetime(lanuch_time))
        while count < (1000*50):
            self.demo_print("================================================")
            count += 1
            try:
                ma5, ma10 = get_MA5_MA10(symbol)
                self.demo_print("Time = %s" % timeStamp_to_datetime(int(time.time())))
                self.demo_print(" MA5 = %s" % ma5)
                self.demo_print("MA10 = %s" % ma10)
                if ma5 > ma10 and last_delta is not None:
                    if last_delta <= 0.0:
                        self.demo_print("CATCH Up cross")
                        last_delta = ma5 - ma10
                        self.demo_print("last_delta = %s" % last_delta)
                        # 出现上涨信号，开始获取 base 价格
                        up_trend = True
                        down_trend = False
                        # 输出 base 的价格
                        _, up_cross_price = get_current_price(symbol)
                        self.demo_print("Up Cross: %s = %s" % (symbol, up_cross_price))
                    else:
                        last_delta = ma5 - ma10
                        if up_trend:
                            self.demo_print("IN Up Trend")
                            self.demo_print("last_delta = %s" % last_delta)
                            _, cur_price = get_current_price(symbol)
                            self.demo_print("%s = %s" % (symbol, cur_price))
                            self.demo_print("up_cross %s = %s" % (symbol, up_cross_price))
                            assert up_cross_price > 0.0
                            up_rate = (cur_price - up_cross_price) / up_cross_price
                            self.demo_print("up_rate = %s" % up_rate)
                elif ma5 < ma10 and last_delta is not None:
                    if last_delta >= 0.0:
                        self.demo_print("CATCH Down cross")
                        last_delta = ma5 - ma10
                        self.demo_print("last_delta = %s" % last_delta)
                        # 出现下跌信号，开始获取 base 的价格
                        up_trend = False
                        down_trend = True
                        # 输出 base 的价格
                        _, down_cross_price = get_current_price(symbol)
                        self.demo_print("Down Cross: %s = %s" % (symbol, down_cross_price))
                        # 输出 up_rate
                        if up_cross_price > 0.0:
                            up_rate = (cur_price - up_cross_price) / up_cross_price
                            self.demo_print("up_rate = %s" % up_rate)
                            total_up_rate += up_rate
                            self.demo_print("total_up_rate = %s" % total_up_rate)
                    else:
                        last_delta = ma5 - ma10
                elif last_delta is None:
                    last_delta = ma5 - ma10
                else:
                    assert False
            except Exception as ex:
                self.demo_print("Exception in output_MA5_MA10_base!")
                self.demo_print("EX: %s" % ex)

hbgAnyCall = HbgAnyCall()

logger = logging.getLogger("demo")
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler("demo.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# 获取指定交易对的下单精度
def Get_orderamount_precision(symbol="btc3lusdt"):
    orderamount_precision = 4
    # if symbol in (
    #         "btc3lusdt", "btc3susdt",
    # ):
    #     orderamount_precision = 4
    # elif symbol in ():
    #     orderamount_precision = 8
    return orderamount_precision


# 基于精度和截断方式做数据截断
def decimals_accuracy_n(inputDecimals, n_bits=4, accuracy_type='trunc'):
    outDecimals = inputDecimals
    try:
        if n_bits < 1:
            n_bits = 1
        if n_bits > 20:
            n_bits = 20
        s_bits = '1'
        for i in range(0, n_bits):
            s_bits += '0'
        outDecimals = Decimal(str(inputDecimals)) * Decimal(s_bits)
        if accuracy_type == 'round':
            outDecimals = round(outDecimals)
        elif accuracy_type == 'floor':
            outDecimals = math.floor(outDecimals)
        elif accuracy_type == 'ceil':
            outDecimals = math.ceil(outDecimals)
        else:
            outDecimals = math.trunc(outDecimals)
        outDecimals = Decimal(outDecimals) / Decimal(s_bits)
        outDecimals = float(outDecimals)
    except Exception as ex:
        print("Exception in decimals_accuracy_n")
        print("ex= %s" % ex)
    return outDecimals

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


# 等待至下一个X分钟的开始
def wait_to_X_min_begin(x=5):
    time_stamp = int(time.time())
    sleep_seconds = (60*5) - (time_stamp % (60*5))
    time.sleep(sleep_seconds)
    return True

# 获取MA5
def get_MA5_MA10(symbol="ethusdt"):
    ma5 = 0.0
    ma10 = 0.0
    # print("Time = %s" % timeStamp_to_datetime(int(time.time())))
    wait_to_X_min_begin(x=5)
    ret = Get_kline_data(
        symbol=symbol,
        period="5min",
        size=11
    )
    assert ret["status"] == "ok"
    ret_data = ret["data"]
    count = 0
    close_price = 0.0
    for item in ret_data:
        if count == 0:
            count += 1
            continue
        else:
            close_price += item["close"]
            if count == 5:
                ma5 = close_price / count
                ma5 = round(ma5, 6)
            count += 1
    ma10 = close_price / (count-1)
    ma10 = round(ma10, 6)
    # print("ma5=%s" % ma5)
    # print("ma10=%s" % ma10)
    return ma5, ma10

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

# 查询订单详情
# API Key 权限：读取
# 限频值（NEW）：50次/2s
# 此接口返回指定订单的最新状态和详情。通过API创建的订单，撤销超过2小时后无法查询。
def Get_orders_details(
        access_key, secret_key,
        order_id,  # 订单ID，填在path中
):
    params = {
        "order-id": order_id,  # 填在 path 中，取值参考 GET /v1/account/accounts
    }
    interface_path = "/v1/order/orders/%s" % order_id
    return HbgAnyCall().callApiMethod(
        access_key=access_key, secret_key=secret_key,
        host_path="https://api.huobi.pro",
        interface_path=interface_path,
        method_type="GET",
        headers=None,
        params=params
    )

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
            period=period,
            size=2000,
        )
        Total_earn_value_ALL_A += earn_value_ALL_A
        Total_earn_value_ALL_B += earn_value_ALL_B
    demo_print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    demo_print("Total_earn_value_ALL_A = %s " % Total_earn_value_ALL_A)
    demo_print("Total_earn_value_ALL_B = %s " % Total_earn_value_ALL_B)

def demo_06():
    print(timeStamp_to_datetime(int(time.time())))
    k_line_res = Get_kline_data(
        symbol="btcusdt",
        period="5min",
        size=1000
    )
    k_line_res = Get_kline_data(
        symbol="btc3lusdt",
        period="5min",
        size=1000
    )
    k_line_res = Get_kline_data(
        symbol="btc3susdt",
        period="5min",
        size=1000
    )
    # print(k_line_res)
    print(timeStamp_to_datetime(int(time.time())))


def demo_03():
    # response = Get_market_trade(symbol="btc3lusdt")
    time_stamp = int(time.time())
    dt_stamp = timeStamp_to_datetime(time_stamp)
    demo = DemoStrategy()
    # ret, response = \
    #     demo.actual_buy_market_level_coins("bch3susdt", "bch3s")
    # print(response)
    response = Get_orders_details(
        access_key=demo.access_key,
        secret_key=demo.secret_key,
        order_id="221672635169587"
    )
    print(response)

    response = Get_orders_matchresults(
        access_key=demo.access_key,
        secret_key=demo.secret_key,
        order_id="221672635169587"
    )
    print(response)

    # buy
    # sell
    # print(response)

def demo_Api(access_key, secret_key):
    response = API_v2_account_repayment(access_key, secret_key)
    hbgAnyCall = HbgAnyCall()
    hbgAnyCall.print_json(response)


# def demo_02():
#     etp = "btc"
#     # etp = "bch"
#     # etp = "ltc"
#     period = "5min"  # 1min, 5min, 15min, 30min
#     size = 2000
#     trend_base_list = get_symbol_trend_data(
#         symbol=(etp + "usdt"),
#         period=period,
#         size=size,
#     )
#     trend_3l_list = get_symbol_trend_data(
#         symbol=(etp + "3lusdt"),
#         period=period,
#         size=size,
#     )
#     trend_3s_list = get_symbol_trend_data(
#         symbol=(etp + "3susdt"),
#         period=period,
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
        # balance = Get_currency_balance(
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

# 基于K线的计算
# def calculate_base_on_KLine(
#         symbol_base="btcusdt",
#         symbol_l="btc3lusdt",
#         symbol_s="btc3susdt",
#         period="1min",
#         size=2000,
#     ):
#     trend_base_list, trend_3l_list, trend_3s_list \
#         = get_ALL_symbol_trend_data(
#         symbol_base=symbol_base,
#         symbol_l=symbol_l,
#         symbol_s=symbol_s,
#         period=period,
#         size=size,
#     )
#     earn_value_ALL_A = 0
#     earn_value_ALL_B = 0
#     try:
#         calculate_trend_data(
#             trend_base_list=trend_base_list,
#             trend_3l_list=trend_3l_list,
#             trend_3s_list=trend_3s_list,
#             symbol_base=symbol_base,
#             start_point=1500,
#             end_point=1000,
#         )
#         earn_value_Half_B = plan_B(symbol_base, size, int(size / 2), trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_Half_B = %s" % (symbol_base, earn_value_Half_B), ignore=False)
#         earn_value_C_B = plan_B(symbol_base, int(size / 2), 1, trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_C_B = %s" % (symbol_base, earn_value_C_B), ignore=False)
#         earn_value_ALL_B = plan_B(symbol_base, size, 1, trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_ALL_B = %s" % (symbol_base, earn_value_ALL_B), ignore=False)
#         earn_value_Half_A = plan_A(symbol_base, size, int(size / 2), trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_Half_A = %s" % (symbol_base, earn_value_Half_A), ignore=False)
#         earn_value_D_A = plan_A(symbol_base, int(size / 2), 1, trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_D_A = %s" % (symbol_base, earn_value_D_A), ignore=False)
#         earn_value_ALL_A = plan_A(symbol_base, size, 1, trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_ALL_A = %s" % (symbol_base, earn_value_ALL_A), ignore=False)
#         hbgAnyCall.log_print("。。。%s: ALL_A + ALL_B = %s" % (symbol_base, earn_value_ALL_A+earn_value_ALL_B), ignore=False)
#         demo_print("****************************************************************************")
#         calculate_trend_data(
#             trend_base_list=trend_base_list,
#             trend_3l_list=trend_3l_list,
#             trend_3s_list=trend_3s_list,
#             symbol_base=symbol_base,
#             start_point=500,
#             end_point=0,
#         )
#         earn_value_C_B_2 = plan_B(symbol_base, int(size / 4), 1, trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_C_B_2 = %s" % (symbol_base, earn_value_C_B_2), ignore=False)
#         earn_value_D_A_2 = plan_A(symbol_base, int(size / 4), 1, trend_base_list, trend_3l_list, trend_3s_list)
#         hbgAnyCall.log_print("%s: earn_value_D_A_2 = %s" % (symbol_base, earn_value_D_A_2), ignore=False)
#     except Exception as ex:
#         demo_print("Exception in calculate_base_on_KLine")
#         demo_print(ex)
#     return earn_value_ALL_A, earn_value_ALL_B