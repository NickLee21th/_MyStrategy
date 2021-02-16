import datetime
import time
import threading
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
from project.demos.demo import *


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
        # demo_03()
        time_stamp = int(time.time())
        dt_stamp = timeStamp_to_datetime(time_stamp)
        demo = DemoStrategy()
        demo.etp = "btc"
        demo.dt_stamp = dt_stamp
        demo.demon_action()

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