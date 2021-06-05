import logging
import time
import json
import os.path
from project.demos.Base_Api import *

class Strategy_Base:
    demo_logger = None
    symbol = "ethusdt"
    period = "5min"
    buy_min_quoter_amount = 6  # 买入时最小的 quoter 下单数量
    run_days = 2
    bPrintLog = True
    log_file_path = ""
    log_folder_name = ""
    log_file_template = ""
    log_dt_stamp = ""

    # 等待至下一个X分钟的开始
    def wait_to_next_X_min_begin(self, x=5):
        try:
            time_stamp = int(time.time())
            sleep_seconds = (60 * x) - (time_stamp % (60 * x))
            time.sleep(sleep_seconds)
            return True
        except Exception as ex:
            self.log_print("Exception in wait_to_next_X_min_begin")
            self.log_print("ex: %s" % ex)
            return False

    # 获取K线数据
    def get_kline_data(
            self,
            symbol="ethusdt",
            period="5min",
            size=3
    ):
        try:
            ret = Get_kline_data(
                symbol=symbol,
                period=period,
                size=size
            )
            assert ret["status"] == "ok"
            ret_data = ret["data"]
            return ret_data
        except Exception as ex:
            self.log_print("Exception in get_kline_data")
            self.log_print("ex: %s" % ex)
            return False

    # 获取第一个买入卖出价格
    def get_first_price(self):
        ret = Get_market_depth(
            symbol=self.symbol
        )
        assert ret["status"] == "ok"
        first_buy_price = ret["tick"]["bids"][0][0]
        first_sell_price = ret["tick"]["asks"][0][0]
        return first_buy_price, first_sell_price

    def logger_init(self,
                    log_folder_name="",
                    log_file_template="",
                    dt_stamp=""
                    ):
        logger = logging.getLogger(self.symbol)
        logger.setLevel(level=logging.INFO)
        dt_value = dt_stamp
        log_file_name = log_file_template % (dt_value, self.symbol)
        self.log_file_path = log_folder_name+log_file_name
        self.log_folder_name = log_folder_name
        self.log_file_template = log_file_template
        self.log_dt_stamp = dt_stamp
        handler = logging.FileHandler(self.log_file_path)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.demo_logger = logger

    def log_print(self, log, ignore=False, end=None):
        if not os.path.isfile(self.log_file_path):
            self.logger_init(
                log_folder_name=self.log_folder_name,
                log_file_template=self.log_file_template,
                dt_stamp=self.log_dt_stamp
            )
        if not self.bPrintLog:
            return
        if ignore:
            log = None
        if log is not None:
            self.demo_logger.info(str(log))
            if end is not None:
                print(str(log), end=end)
            else:
                print(str(log))

    def json_print(self, json_str):
        if self.bPrintLog:
            str_json_format = json.dumps(json_str, indent=4, sort_keys=True, ensure_ascii=False)
            logging.info(str(str_json_format))
            print(str(str_json_format))