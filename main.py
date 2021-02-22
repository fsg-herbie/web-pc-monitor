#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import executes
import api
import multiprocessing as mp

if __name__ == '__main__':

    print("程序开始执行,时间：" + time.ctime())

    # 定义一个进程池
    po = mp.Pool(60)

    while True:
        # 延迟执行避免占用过多资源
        time.sleep(15)

        # 查询设备状态
        device_data = api.init_check()
        if not device_data:
            continue

        # 查询订单队列
        find_task_order = api.find_up_task(device_data['device_id'])
        if not find_task_order:
            continue

        # 更新任务状态，避免多次调用
        update_task_order = api.update_task_order(find_task_order['task_id'], 1)
        if not update_task_order:
            continue

        try:
            po.apply_async(executes.entrance, args=(device_data, update_task_order,))
        except:
            api.update_task_order(find_task_order['task_id'], 6)
            continue

    # 程序结束下线所有帐号
    api.down_account_all()
