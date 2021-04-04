import datetime
import time
import threading
from multiprocessing import Pool, Manager
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
from project.demos.demo import *
import sys


# UNIX时间戳 转换为 datetime  显示
def timeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d-%H-%M-%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)

if __name__ == '__main__':
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    # hbgAnyCall = HbgAnyCall()
    try:
        # demo = DemoStrategy()
        # argvs = sys.argv
        # if len(argvs) > 1:
        #     symbol = argvs[1]
        # if len(argvs) > 2:
        #     base = argvs[2]
        # # demo.output_MA5_MA10(symbol=symbol, base=base)
        # demo.output_MA5_MA10_base(symbol=symbol)

        demoStrategy = DemoStrategy()
        first_buy_price, first_buy_size \
            = demoStrategy.get_symbol_first_buy_price(symbol="link3lusdt")
        print("first_buy_price=%s  first_buy_size=%s" % (first_buy_price, first_buy_size))
        first_sell_price, first_sell_size \
            = demoStrategy.get_symbol_first_sell_price(symbol="link3lusdt")
        print("first_sell_price=%s  first_sell_size=%s" % (first_sell_price, first_sell_size))

        #demo_06()

        # time_stamp = int(time.time())
        # dt_stamp = timeStamp_to_datetime(time_stamp)
        # queue = Manager().Queue(10)
        # demo = DemoStrategy()
        # demo.queue = queue
        # demo.etp = "bch"
        # demo.dt_stamp = dt_stamp
        # log_folder_name = "Demo_before_launch_01"
        # demo.demon_action(log_folder_name)

        # demo.demon_prediction()

        # demo_01()
        # demo_02()
        # demo_03()
        # demo_Api(access_key, secret_key)
        # main_demo("btc")

        # 多线程处理
        # for etp in (
        #         "btc",
        #         "eth", "link",
        #         "eos", "bch", "ltc",
        #         "zec", "xrp",
        #         "bsv", "fil",
        # ):
        #     demo = DemoStrategy()
        #     demo.etp = etp
        #     t = threading.Thread(
        #         target=demo.demon_main,
        #         # args={etp}
        #     )
        #     t.start()
    except Exception as ex:
        print("Exception in main")
        hbgAnyCall.log_print(ex, ignore=False)