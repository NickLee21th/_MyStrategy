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

    def do_strategy_execute(self, symbol, dt_stamp):
        try:
            self.symbol = symbol
            self.logger_init(
                log_folder_name="Strategy_01_log",
                log_file_template="/Strategy_01_%s_%s.log",
                dt_stamp=dt_stamp
            )
            self.log_print("HERE I AM!")
            ret_data = self.get_kline_data(
                symbol=symbol,
                period="5min"
            )
            self.json_print(ret_data)
        except Exception as ex:
            self.log_print("Exception in do_strategy_execute")
            self.log_print("ex: %s" % ex)


if __name__ == '__main__':
    time_stamp = int(time.time())
    dt_stamp = TimeStamp_to_datetime(time_stamp)
    my_strategy = Strategy_01()
    my_strategy.do_strategy_execute(
        symbol="ethusdt",
        dt_stamp=dt_stamp
    )

