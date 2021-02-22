#!/usr/bin/python3
# -*- coding: utf-8 -*-

import function as func
import json

# 接口主域名
host = "https://localhost"

# 支付宝登录页面
aliPayLoginUrl = "https://my.alipay.com/portal/i.htm"


# 全局返回方法
def return_data(result):
    if not result:
        return False
    if result is None:
        return False

    if int(result['status']) != 1:
        return False
    return result['data']


# 获取远程配置
def get_config():
    url = host + "/api/pc_monitor/get_config"
    result = func.curl(url, "post")
    return return_data(result)


# 获取代理IP
def get_proxy_config(device_id, task_id):
    url = host + "/api/pc_monitor/get_proxy_config"
    result = func.curl(url, "post", {"device_id": device_id, "task_id": task_id})
    return return_data(result)


# 开机效验
def init_check():
    url = host + "/api/pc_monitor/init_check"
    param = {"mac": func.get_mac_address(), "name": func.get_hostname(), "ip": func.get_ip_address(),
             "system": func.get_sys_platform()}
    result = func.curl(url, "post", param)
    return return_data(result)


# 查询上号订单任务
def find_up_task(device_id):
    url = host + "/api/pc_monitor/get_task_order"
    result = func.curl(url, "post", {"device_id": device_id})
    return return_data(result)


# 更新任务状态
def update_task_order(task_id, status, param=None):
    url = host + "/api/pc_monitor/update_task_order"
    if not param:
        param = {"task_id": task_id, "status": status}
    else:
        param = {"task_id": task_id, "status": status, "param": json.dumps(param)}

    result = func.curl(url, "post", param)
    return return_data(result)


def get_account_info(account_id):
    url = host + "/api/pc_monitor/get_account_info"
    result = func.curl(url, "post", {"account_id": account_id})
    return return_data(result)


# 账户上线
def up_account(account_id):
    url = host + "/api/pc_monitor/up_account"
    result = func.curl(url, "post", {"account_id": account_id})
    return return_data(result)


# 帐号下线
def down_account(account_id):
    url = host + "/api/pc_monitor/down_account"
    result = func.curl(url, "post", {"account_id": account_id})
    return return_data(result)


# 全部下线
def down_account_all():
    url = host + "/api/pc_monitor/down_account_all"
    result = func.curl(url, "post")
    return return_data(result)


# 查询订单
def find_order(account_id, task_id):
    url = host + "/api/pc_monitor/find_account_order"
    result = func.curl(url, "post", {"account_id": account_id, "task_id": task_id})
    return return_data(result)


# 推送消息
def pull_message(version_types, task_data, order, msg_data):
    url = host + "/api/pc_monitor/pull_message"

    param = {
        "version_types": version_types,
        "task_id": task_data['task_id'],
        "account_id": task_data['account_id'],
        "user_id": task_data['user_id'],
        "order_id": order['order_id'],
        "amount": order['amount'],
        "msg_data": json.dumps(msg_data, ensure_ascii=False),
    }

    result = func.curl(url, "post", param)
    return return_data(result)
