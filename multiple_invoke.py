#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import time
import multiprocessing
from multiprocessing import Pool, Manager
import subprocess
import os, time, random
import sys
from project.demos.config import *
from project.demos.demo import *

current_path = os.path.dirname(os.path.abspath(__file__))

# UNIX时间戳 转换为 datetime  显示
def timeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d-%H-%M-%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)

def schedule_job(etp, dt_stamp,queue=None,log_folder_name=None):
    access_key = ACCESS_KEY
    secret_key = SECRET_KEY
    account_id = ACCOUNT_ID  # spot
    try:
        demo = DemoStrategy()
        demo.queue = queue
        demo.etp = etp
        demo.dt_stamp = dt_stamp
        demo.access_key = access_key
        demo.secret_key = secret_key
        demo.account_id = account_id
        demo.demon_action(log_folder_name)
        # demo.demon_prediction()
    except Exception as ex:
        print("Exception in schedule_job, etp = %s" % etp)
        print("ex=%s" % ex)

def collection_job(queue=None, log_folder_name=None):
    try:
        count = 0
        earn_all = {}
        while True and count < 6*30:
            if queue.empty() is False:
                count = 0
                queue_item = queue.get()
                file_name = log_folder_name + "_collextion.txt"
                data = open(file_name, 'a')
                try:
                    key = queue_item["action_index"]
                    if key in earn_all.keys():
                        symbol = queue_item["symbol"]
                        earn_all[key][symbol] = queue_item
                        earning_ratio = queue_item["earning_ratio"]
                        earn_all[key]["earning_ratio_ALL"] += earning_ratio
                        current_balance = queue_item["current_balance"]
                        earn_all[key]["current_balance_ALL"] += current_balance
                        actual_balance = queue_item["actual_balance"]
                        earn_all[key]["actual_balance_ALL"] += actual_balance
                        earn_all[key][queue_item["symbol"] + "_stop_actual_invest"] \
                            = queue_item["stop_actual_invest"]
                        earn_all[key]['count'] += 1
                        print("earn_all[%s]['count']  = %s" % (key, earn_all[key]['count']))
                        if earn_all[key]['count'] >= 10:
                            print("===================================================", file=data)
                            print({
                                "RUN_TIME": key,
                                "earn_all": earn_all[key],
                            }, file=data)
                            print("===================================================", file=data)
                    else:
                        earn_all[key] = {
                            "count": 1,
                            "earning_ratio_ALL": queue_item["earning_ratio"],
                            "current_balance_ALL": queue_item["current_balance"],
                            queue_item["symbol"]+"_stop_actual_invest": queue_item["stop_actual_invest"],
                            "actual_balance_ALL": queue_item["actual_balance"],
                        }
                        symbol = queue_item["symbol"]
                        earn_all[key][symbol] = queue_item
                        print("earn_all[%s]['count']  = %s" % (key, earn_all[key]['count']))
                except Exception as ex:
                    print("Exception when print queue_item")
                    print("ex=%s" % ex)
                data.close()
            else:
                count += 1
            time.sleep(10)
    except Exception as ex:
        print("Exception in collection_job")
        print("ex=%s" % ex)

def long_time_task(etp, dt_stamp, queue, log_folder_name):
    print('Run task %s (%s)...' % (etp, os.getpid()))
    start = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (start= %s)...' % (etp, start))
    # cmd = 'python3 schedule_job.py %s %s' % (etp, dt_stamp)
    # os.system(cmd)
    schedule_job(etp=etp, dt_stamp=dt_stamp, queue=queue,log_folder_name=log_folder_name)
    end = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (end= %s)...' % (etp, end))

def long_time_task_2(queue, log_folder_name):
    print('Run COLLECTION task  (%s)...' % os.getpid())
    start = timeStamp_to_datetime(int(time.time()))
    print('Run COLLECTION task (start= %s)...' % start)
    collection_job(queue=queue,log_folder_name=log_folder_name)
    end = timeStamp_to_datetime(int(time.time()))
    print('Run COLLECTION task (end= %s)...' % end)

def multi_process(dt_stamp, log_folder_name):
    print('Parent process %s.' % os.getpid())
    process_pool_size = 11
    queue = Manager().Queue(process_pool_size * 2)
    p = Pool(process_pool_size)
    for etp in (
            "btc", "eth", "link",
            "eos", "bch", "ltc",
            "zec", "xrp", "bsv", "fil",
    ):
        p.apply_async(long_time_task, args=(etp, dt_stamp, queue, log_folder_name))
    p.apply_async(long_time_task_2, args=(queue, log_folder_name))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.\n')

def multi_process_predict(dt_stamp, log_folder_name):
    print('Parent process %s.' % os.getpid())
    process_pool_size = 11
    queue = Manager().Queue(process_pool_size * 2)
    p = Pool(process_pool_size)
    for etp in (
            "btc", "eth", "link",
            "eos", "bch", "ltc",
            "zec", "xrp", "bsv", "fil",
    ):
        p.apply_async(long_time_task, args=(etp, dt_stamp, queue, log_folder_name))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.\n')

def calculate_total(dt_stamp):
    earn_value_total = 0.0
    total_file_path = "demo_Total_Earn.log"
    file_handle = open(total_file_path, "a")
    try:
        for etp in (
                "btc", "eth",
                "link",
                "eos", "bch", "ltc",
                "zec", "xrp",
                "bsv", "fil",
        ):
            file_path = "demo_log/demo_%s_%s.log" % (dt_stamp, etp)
            file = open(file_path, 'r')
            for line in file.readlines():
                earn_value_str = "earn_value = "
                index_find = line.find(earn_value_str)
                if index_find > 0:
                    earn_value = line[index_find + len(earn_value_str):]
                    earn_value_total += float(earn_value)
                    print("%s earn_value = %s" % (etp, earn_value))
                    print("%s earn_value = %s" % (etp, earn_value), file=file_handle)
                    break
        print("========================================", file=file_handle)
        print("========================================")
        print("%s  earn_value_total = %s" % (dt_stamp, earn_value_total), file=file_handle)
        print("%s  earn_value_total = %s" % (dt_stamp, earn_value_total))
        print("========================================\n", file=file_handle)
        print("========================================\n")
    except Exception as ex:
        print("Exception in calculate_total")
        print("ex = %s" % ex)
    file_handle.close()

def consumer():
    r = ''
    while True:
        n = yield r
        if not n:
            return
        print('[CONSUMER] Consuming %s...' % n)
        r = '200 OK'


def produce(c):
    c.send(None)
    n = 0
    while n < 5:
        n = n + 1
        print('[PRODUCER] Producing %s...' % n)
        r = c.send(n)
        print('[PRODUCER] Consumer return: %s' % r)
    c.close()


def fiber_mode(name):
    print('fiber %s START' % name)
    c = consumer()
    produce(c)
    print('fiber %s FINISH' % name)

# nohup python3 multiple_invoke.py run_action_02_25_log >output_02 2>&1 &
if __name__=='__main__':
    count = 0
    time_stamp = int(time.time())
    dt_stamp = timeStamp_to_datetime(time_stamp)

    log_folder_name = "demo_action_log"
    argvs = sys.argv
    if len(argvs) > 1:
        log_folder_name = argvs[1]
    cmd = 'mkdir %s' % log_folder_name
    os.system(cmd)
    multi_process(dt_stamp, log_folder_name)

    # while True:

    # while count < 1:  # 1000:
    #     time_stamp = int(time.time())
    #     dt_stamp = timeStamp_to_datetime(time_stamp)
    #     multi_process_predict(dt_stamp, "")
    #     calculate_total(dt_stamp)
    #     time_stamp_end = int(time.time())
    #     sleep_time = 60*5 - (time_stamp_end - time_stamp)
    #     if sleep_time > 0:
    #         print("sleep %s seconds ....." % sleep_time)
    #         # time.sleep(sleep_time)
    #     count += 1
