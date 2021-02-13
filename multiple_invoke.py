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

def long_time_task(etp):
    print('Run task %s (%s)...' % (etp, os.getpid()))
    start = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (start= %s)...' % (etp, start))
    cmd = 'python3 schedule_job.py %s' % etp
    os.system(cmd)
    end = timeStamp_to_datetime(int(time.time()))
    print('Run task %s (end= %s)...' % (etp, end))


def multi_process():
    print('Parent process %s.' % os.getpid())
    process_pool_size = 10
    p = Pool(process_pool_size)
    for etp in (
            "btc",
            "eth", "link",
            "eos", "bch", "ltc",
            "zec", "xrp",
            "bsv", "fil",
    ):
        p.apply_async(long_time_task, args={etp})
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')

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
    multi_process()
