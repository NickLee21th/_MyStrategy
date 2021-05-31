import time
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.Strategy_01 import *
import sys

if __name__ == '__main__':
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    # hbgAnyCall = HbgAnyCall()
    try:
        symbol = "ethusdt"
        period = "5min"
        run_days = 2
        increasing_price_rate = 0.01
        buy_min_quoter_amount = 6.0
        argvs = sys.argv
        if len(argvs) > 1:
            symbol = argvs[1]
        if len(argvs) > 2:
            period = argvs[2]
        if len(argvs) > 3:
            run_days = float(argvs[3])
        if len(argvs) > 4:
            increasing_price_rate = float(argvs[4])
        if len(argvs) > 5:
            buy_min_quoter_amount = float(argvs[5])
        time_stamp = int(time.time())
        dt_stamp = TimeStamp_to_datetime(time_stamp)
        my_strategy = Strategy_01()
        my_strategy.init_all()
        my_strategy.increasing_price_rate = increasing_price_rate
        my_strategy.do_strategy_execute(
            symbol=symbol,
            period=period,
            run_days=run_days,
            buy_min_quoter_amount=buy_min_quoter_amount,
            dt_stamp=dt_stamp
        )
    except Exception as ex:
        print("Exception in main")
        HbgAnyCall().log_print(ex, ignore=False)