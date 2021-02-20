#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import time
from multiprocessing import Pool
import subprocess
import os, time, random
import unittest

current_path = os.path.dirname(os.path.abspath(__file__))

# UNIX时间戳 转换为 datetime  显示
def timeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d-%H-%M-%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)

def long_time_task(etp, dt_stamp):
    print('Run task %s (%s)...' % (etp, os.getpid()))
    start = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (start= %s)...' % (etp, start))
    cmd = 'python3 schedule_job.py %s %s' % (etp, dt_stamp)
    os.system(cmd)
    end = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (end= %s)...' % (etp, end))


def multi_process(dt_stamp):
    print('Parent process %s.' % os.getpid())
    process_pool_size = 10
    p = Pool(process_pool_size)
    for etp in (
            "btc", "eth",
            "link",
            "eos", "bch", "ltc",
            "zec", "xrp",
            "bsv", "fil",
    ):
        p.apply_async(long_time_task, args=(etp, dt_stamp))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')

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
            file_path = "demo_log/demo_%s_%s.log" % (etp, dt_stamp)
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

if __name__=='__main__':
    count = 0

    time_stamp = int(time.time())
    dt_stamp = timeStamp_to_datetime(time_stamp)
    multi_process(dt_stamp)
    calculate_total(dt_stamp)

    # while True:
    # while count < 1000:
    #     time_stamp = int(time.time())
    #     dt_stamp = timeStamp_to_datetime(time_stamp)
    #     multi_process(dt_stamp)
    #     calculate_total(dt_stamp)
    #     time_stamp_end = int(time.time())
    #     sleep_time = 60*5 - (time_stamp_end - time_stamp)
    #     if sleep_time > 0:
    #         print("sleep %s seconds ....." % sleep_time)
    #         time.sleep(sleep_time)
    #     count += 1
