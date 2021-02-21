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
        while self.queue.empty() is False:
            print('cur pid:', self.process_num, ' queue_url:', self.queue.get()['url'])
            # 模拟每条记录处理的时长
            rand_sleep = random.randint(1, 6)
            time.sleep(rand_sleep)

        print('cur pid:', self.process_num, ' queue: is empty')


def start_spider(queue):
    p1 = Spider(queue)
    p1.run()


def error_test(name):
    print("[子进程%s]PID=%d, PPID=%d" % (name, os.getpid(), os.getppid()))
    raise Exception("[子进程%s]我挂了" % name)


process_num = 4  # 模拟需要使用的进程数
record_len = 10  # 模拟需要处理的记录条数
if __name__ == '__main__':
    q = Manager().Queue(record_len)
    # 将待处理数据依次存入队列中
    for i in range(record_len):
        q.put({'id': i, 'url': 'http://www.lbelieve.cn/id/' + str(i)})

    if q.qsize():
        p = Pool(process_num)
        for i in range(process_num):
            p.apply_async(
                start_spider,
                args=(q,),
                callback=None,
                error_callback=None)
        p.close()
        p.join()
        print("over")