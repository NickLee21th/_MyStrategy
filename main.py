import datetime
import threading
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
from project.demos.demo import *

if __name__ == '__main__':
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    hbgAnyCall = HbgAnyCall()
    try:
        # demo_01()
        # demo_02()
        # demo_03()
        # demo_Api(access_key, secret_key)
        # main_demo("btc")

        # 多线程处理
        for etp in (
                "btc",
                "eth", "link",
                "eos", "bch", "ltc",
                "zec", "xrp",
                "bsv", "fil",
        ):
            demo = DemoStrategy()
            demo.etp = etp
            t = threading.Thread(
                target=demo.demon_main,
                # args={etp}
            )
            t.start()
    except Exception as ex:
        print("Exception in main")
        hbgAnyCall.log_print(ex, ignore=False)