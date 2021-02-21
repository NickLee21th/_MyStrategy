# -*- coding=utf-8 -*-
import time
import sys, os
import random
import multiprocessing
from multiprocessing import Pool, Manager


class Spider(multiprocessing.Process):
    def __init__(self, queue):
        self.queue = queue
        multiprocessing.Process.__init__(self)
        self.process_num = os.getpid()

    def run(self):
        count = 0
        # while self.queue.empty() is False:
        while count < 10:
            count += 1
            print('In Spider, cur pid:', self.process_num, ' count:', count)
            # self.queue.get()['url']
            self.queue.put({'id': self.process_num, 'url': 'http://www.lbelieve.cn/id/' + str(count)})
            # 模拟每条记录处理的时长
            rand_sleep = random.randint(1, 6)
            time.sleep(rand_sleep)
        print('QUIT In Spider, cur pid:', self.process_num,)

def start_spider(queue):
    p1 = Spider(queue)
    p1.run()

class Summary(multiprocessing.Process):
    def __init__(self, queue):
        self.queue = queue
        multiprocessing.Process.__init__(self)
        self.process_num = os.getpid()

    def run(self):
        count = 0
        while True and count < 10:
            if self.queue.empty() is False:
                print('IN Summary, cur pid:', self.process_num,)
                queue_item = self.queue.get()
                print("IN Summary, queue_item: \n%s" % queue_item)
            else:
                print('IN Summary, cur pid:', self.process_num, ' queue: is empty')
                count += 1
            # 模拟每条记录处理的时长
            rand_sleep = random.randint(1, 6)
            time.sleep(rand_sleep)
        print('QUIT IN Summary, cur pid:', self.process_num, )

def start_summary(queue):
    p2 = Summary(queue)
    p2.run()


def error_test(name):
    print("[子进程%s]PID=%d, PPID=%d" % (name, os.getpid(), os.getppid()))
    raise Exception("[子进程%s]我挂了" % name)


process_num = 4  # 模拟需要使用的进程数
record_len = 10  # 模拟需要处理的记录条数
if __name__ == '__main__':
    q = Manager().Queue(record_len)
    # 将待处理数据依次存入队列中
    # for i in range(record_len):
    #     q.put({'id': i, 'url': 'http://www.lbelieve.cn/id/' + str(i)})

    # if q.qsize():
    p = Pool(process_num)
    for i in range(process_num-1):
        p.apply_async(
            start_spider,
            args=(q,),
            callback=None,
            error_callback=None)
    p.apply_async(
        start_summary,
        args=(q,),
        callback=None,
        error_callback=None)
    p.close()
    p.join()
    print("over")