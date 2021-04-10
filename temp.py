#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import time
import multiprocessing
from multiprocessing import Pool, Manager
import subprocess
import os, time, random
import sys

current_path = os.path.dirname(os.path.abspath(__file__))


# UNIX时间戳 转换为 datetime  显示
def timeStamp_to_datetime(timeStamp, dt_format=None):
    if dt_format is None:
        dt_format = "%Y-%m-%d-%H-%M-%S"
    return datetime.datetime.fromtimestamp(timeStamp).strftime(dt_format)

def schedule_job():

    try:
    except Exception as ex:
        print("Exception in schedule_job,")
        print("ex=%s" % ex)


def long_time_task(etp, dt_stamp, queue, log_folder_name, history_size,
                   threshold_value_adjust_rate):
    print('Run task %s (%s)...' % (etp, os.getpid()))
    start = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (start= %s)...' % (etp, start))
    # cmd = 'python3 schedule_job.py %s %s' % (etp, dt_stamp)
    # os.system(cmd)
    schedule_job()
    end = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (end= %s)...' % (etp, end))


def multi_process():
    print('Parent process %s.' % os.getpid())
    process_pool_size = 1000
    # queue = Manager().Queue(process_pool_size * 2)
    p = Pool(process_pool_size)
    for i in range(0, process_pool_size):
        p.apply_async(long_time_task,
                      args=())
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.\n')



# nohup python3 multiple_invoke.py run_action_02_25_log >output_02 2>&1 &
if __name__=='__main__':
    count = 0
    time_stamp = int(time.time())
    dt_stamp = timeStamp_to_datetime(time_stamp)

    log_folder_name = "demo_action_log"
    cmd = 'mkdir %s' % log_folder_name
    os.system(cmd)
    multi_process()


