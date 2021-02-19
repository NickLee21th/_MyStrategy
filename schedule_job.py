import datetime
import threading
from project.demos._hbg_anyCall import HbgAnyCall
from project.demos.config import *
from project.demos.demo import *
import sys
import datetime

if __name__ == '__main__':
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    argvs = sys.argv
    try:
        if len(argvs) > 2:
            demo = DemoStrategy()
            demo.etp = argvs[1]
            demo.dt_stamp = argvs[2]
            demo.access_key = access_key
            demo.secret_key = secret_key
            demo.account_id = account_id
            demo.demon_action()
            # demo.demon_prediction()
    except Exception as ex:
        print("Exception in main, etp = %s" % argvs[1])
        print("ex=%s" % ex)
