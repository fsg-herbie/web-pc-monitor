#!/usr/bin/python3
# -*- coding: utf-8 -*-
from selenium import webdriver
import time
import api
import base64
import random
import function as func


def entrance(device_data, task_data):
    print("接到上号任务%s,时间：%s" % (task_data['task_id'], time.ctime()))
    print(task_data)
    # 定义常用参数
    device_id = device_data['device_id']
    task_id = task_data['task_id']
    user_id = task_data['user_id']
    account_id = task_data['account_id']

    # 是否开启代理
    if int(device_data['is_proxy']) == 1:

        proxy_config = api.get_proxy_config(device_id, task_id)
        if not proxy_config:
            api.update_task_order(task_data['task_id'], 6, {"error_msg": "获取代理配置出错"})
            print("任务ID为 %s 的任务,%s" % (task_data['task_id'], "获取代理配置出错,退出进程"))
            return False

        # 没有可用代理的话就使用本地IP
        if int(proxy_config['to_status']) == 0:
            options = webdriver.ChromeOptions()
            options.add_argument("--log-level=3")
        else:
            proxyauth_plugin_path = func.create_proxyauth_extension(
                proxy_host=proxy_config['ip'],  # 代理服务器ip
                proxy_port=proxy_config['port'],  # 代理服务器端口
                proxy_username=proxy_config['username'],  # 用户名
                proxy_password=proxy_config['password'],  # 密码
                scheme=proxy_config['scheme'],
                plugin_path="./proxy_auth_plugin/%s.zip" % proxy_config['ip']
            )

            options = webdriver.ChromeOptions()
            options.add_argument("--log-level=3")
            options.add_extension(proxyauth_plugin_path)

            time.sleep(2)
            # 传一个IP给数据库好做记录
            api.update_task_order(task_id, task_data['status'], {"bind_ip": proxy_config['ip']})
    else:
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")

    if func.get_sys_platform() == "Linux":
        browser = webdriver.Chrome(executable_path="./webdriver/chromedriver.linux", chrome_options=options)
    elif func.get_sys_platform() == "Darwin":
        browser = webdriver.Chrome(executable_path="./webdriver/chromedriver.mac", chrome_options=options)
    else:
        browser = webdriver.Chrome(executable_path="./webdriver/chromedriver.exe", chrome_options=options)

    time.sleep(1)
    # 获取系统配置
    config = api.get_config()
    if not config:
        return quit_fun(task_data, browser, 6, "获取系统配置出错")
    time.sleep(1)

    # 打开支付宝登录页面
    browser.get(api.aliPayLoginUrl)
    # 设置最长显式等待时间(全局)
    browser.implicitly_wait(3)

    # 回传二维码
    return_qrcode = get_login_qrcode(task_data, browser)
    time.sleep(3)
    if not return_qrcode:
        return quit_fun(task_data, browser, 6, "获取二维码错误")

    # ---------轮询登录状态----------

    # 登录成功获取账户信息
    account_info = api.get_account_info(account_id)
    if not account_info:
        return quit_fun(task_data, browser, 6, "获取帐号信息时发生错误")

    print("任务%s开始轮询登录状态,时间：%s" % (task_data['task_id'], time.ctime()))
    # 设置一个定时器,超过这个时间则为扫码超时
    scan_qrcode_time = 0
    is_login_var = False
    while not is_login_var:
        if not is_window_run(browser):
            return quit_fun(task_data, browser, 6, "窗口已关闭,程序结束")

        time.sleep(3)
        scan_qrcode_time += 3
        # 如果超过指定时间不扫码就退出进程
        if scan_qrcode_time > int(config['web_base.qrocde_out_time']):
            return quit_fun(task_data, browser, 5, "二维码已过期")

        if not is_login(browser, int(account_info['version_types'])):
            is_login_var = False
        else:
            is_login_var = True

    if not is_login_var:
        return quit_fun(task_data, browser, 6, "登录出错")

    time.sleep(2)
    # 验证登陆的是否是同一个账户
    if not checkAccount(browser, account_info['number'], int(account_info['version_types'])):
        print("任务%s验证账号错误，扫码登陆的账号不等于任务账号" % task_data['task_id'])
        return quit_fun(task_data, browser, 6, "验证账号错误，扫码登陆的账号不等于任务账号")

    print("任务%s成功登录,时间：%s" % (task_data['task_id'], time.ctime()))
    time.sleep(2)
    # 关闭弹窗
    try:
        # 查询广告窗口元素
        alipayXbox = browser.find_element_by_css_selector(".alipay-xbox")
        alipayXbox.find_element_by_css_selector(".alipay-xbox-close").click()
        print("任务%s成功关闭了广告窗口" % task_data['task_id'])
    except:
        print("任务%s没有广告窗口" % task_data['task_id'])

    time.sleep(5)
    # 进入账单中心
    if not to_bill_page(browser, int(account_info['version_types'])):
        return quit_fun(task_data, browser, 6, "进入账单中心错误,请管理员检查")

    time.sleep(1)

    # 通知帐号上线
    up_account = api.up_account(account_id)
    if not up_account:
        return quit_fun(task_data, browser, 6, "通知帐号上线发生错误")

    time.sleep(1)

    # 更新任务状态
    api.update_task_order(task_data['task_id'], 3)

    # 设置一个刷新定时器,防止支付宝登录过期
    status_time = int(time.time())

    # 设置一个每次循环所用时间
    for_time = int(time.time())
    print("任务%s监控账单开始运行,时间：%s" % (task_data['task_id'], time.ctime()))
    # print("初始时间 %s" % for_time)
    while True:

        # 查询窗口是否存在
        if not is_window_run(browser):
            return quit_fun(task_data, browser, 6, "窗口已关闭,程序结束")

        # 检查是否在账单页
        if not is_bill_page(browser, int(account_info['version_types'])):
            return quit_fun(task_data, browser, 6, "帐号已不在账单页面,下号避免掉单")

        try:
            if int(time.time()) >= status_time + int(config['web_base.pc_refresh_time']):
                browser.refresh()
                status_time = int(time.time())
        except:
            return quit_fun(task_data, browser, 6, "刷新页面错误，网络出错")

        time.sleep(1)

        # 查询订单
        order = api.find_order(account_id, task_data['task_id'])
        # print("订单数据 %s" % order)
        if not order:
            time.sleep(30)
            for_time = int(time.time())
            print("任务%s,查询没有订单,时间:%s" % (task_data['task_id'], time.ctime()))
            continue

        if int(order['to_status']) == 2:
            return quit_fun(task_data, browser, 7, "帐号已下线")

        if int(account_info['version_types']) == 1:
            msg_status = get_personal_pay_message(browser, int(account_info['version_types']), task_data, order)
            print("任务%s运行的个人版监控" % task_data['task_id'])
        else:
            msg_status = get_company_pay_message(browser, int(account_info['version_types']), task_data, order)
            print("任务%s运行的企业版监控" % task_data['task_id'])

        if not msg_status:
            return quit_fun(task_data, browser, 7, "这个帐号抓取账单时出现错误")

        # 如果运行时间已经大于了当前时间,直接跳过,否则计时
        if int(time.time()) > for_time + int(config['web_base.pc_order_time']):
            # print("大于了运行时间")
            # print("计时时间 %s" % for_time)
            # print("加时间后 %s" % for_time + int(config['web_base.pc_order_time']))
            for_time = int(time.time())
            continue
        else:
            # print("没有大于运行时间")
            # 获取已经过去多少秒
            pc_order_time = int(time.time()) - for_time
            # print("已经过去了 %s 秒" % pc_order_time)
            sleep_time = int(config['web_base.pc_order_time']) - int(pc_order_time)
            # 开始轮询计时
            time.sleep(sleep_time)

        # 重置计时时间
        for_time = int(time.time())

    print("任务ID为%s的任务已经执行完毕" % task_data['task_id'])


# browser 变量必须在 函数之后 否则函数体为null
def quit_fun(task_data, browser, status, error_msg):
    # 更新任务状态
    api.update_task_order(task_data['task_id'], status, {"error_msg": error_msg})
    time.sleep(1)
    # 凡事触发退出的都下线该帐号
    api.down_account(task_data['account_id'])
    browser.quit()
    print("任务ID为 %s 的任务,%s" % (task_data['task_id'], error_msg))
    return False


# 驱动是否还存在
def is_window_run(browser):
    try:
        return browser.title
    except:
        return False


# 是否登录状态
def is_login(browser, version_types):
    try:
        if version_types == 1:
            browser.find_element_by_link_text("退出")
            return True
        else:
            browser.find_element_by_link_text("对账中心")
            return True
    except:
        return False


# 验证账户是否相同
def checkAccount(browser, account, version_types):
    try:
        if version_types == 1:
            element = browser.find_element_by_id("J-userInfo-account-userEmail")
        else:
            element = browser.find_element_by_class_name("home-account-login-name")

        loginAccount = element.text.strip().replace("\n", "").replace("\n", "").replace("\r\n", "")
        print("账号验证打印，抓取账号：%s 填写账号：%s" % (loginAccount, account))
        if loginAccount != account:
            return False

        return True
    except:
        return False


# 是否在首页
def is_index_page(browser, types):
    if int(types) == 1:
        return is_personal_index_page(browser)
    else:
        return is_company_index_page(browser)


# 是否在账单页
def is_bill_page(browser, types):
    if int(types) == 1:
        return is_personal_bill_page(browser)
    else:
        return is_company_bill_page(browser)


# 进入账单中心
def to_bill_page(browser, types):
    try:
        # 判断是企业支付宝还是个人
        if int(types) == 1:

            time.sleep(3)

            try:
                # 点击进入账单监控页面
                browser.find_element_by_link_text("查看").click()
            # 支付宝首页有弹窗的情况
            except:
                return False

        else:

            time.sleep(3)
            browser.find_element_by_link_text("对账中心").click()
            # 企业版需要额外点击一次进入财务中心
            time.sleep(3)
            browser.find_element_by_link_text("账务明细").click()
        return True
    except:
        return False


# 是否在首页页面
def is_personal_index_page(browser):
    try:
        browser.find_element_by_link_text("显示余额")
        return True
    except:
        return False


# 是否在账单页面
def is_personal_bill_page(browser):
    try:
        browser.find_element_by_id("tradeRecords")
        return True
    except:
        return False


# 是否商家首页
def is_company_index_page(browser):
    try:
        title = browser.title
        if title == "支付宝商家中心-国内领先的第三方支付和金融服务平台-首页":
            return True

        return False
    except:
        return False


# 是否商家账单页面
def is_company_bill_page(browser):
    try:
        title = browser.title
        if title == "账务明细":
            return True

        return False
    except:
        return False


# 获取超级版
def get_personal_pay_message(browser, version_types, task_data, order):
    try:

        # 刷新浏览器
        browser.refresh()

        time.sleep(3)

        # 如果不存在 tradeRecords 则不在账单页面
        try:
            table = browser.find_element_by_id("tradeRecords")
        except:
            return False

        # 如果不存在则账单是空的,返回让账单继续轮询
        try:
            trs = table.find_elements_by_css_selector(".record-list")
        except:
            return True

        data = []
        for tr in trs:
            tds = tr.find_elements_by_css_selector("td")
            tr_data = []
            for td in tds:
                tr_data.append(td.text)
            data.append(tr_data)

        # 直接传给服务端处理
        api.pull_message(version_types, task_data, order, data)
        return True

    except:
        return False


# 获取企业支付通知
def get_company_pay_message(browser, version_types, task_data, order):
    try:

        # 刷新浏览器
        browser.refresh()

        time.sleep(3)

        # 不在账单页
        if not is_company_bill_page(browser):
            return False

        # 如果不存在 ant-table-fixed 说明账单是空的
        try:
            table = browser.find_element_by_class_name("ant-table-fixed")
        except:
            return True

        # 如果不存在则账单是空的,返回让账单继续轮询
        try:
            trs = table.find_elements_by_class_name("ant-table-row")
        except:
            return True

        data = []
        for tr in trs:
            tds = tr.find_elements_by_css_selector("td")
            tr_data = []

            tds_i = 0
            for td in tds:
                # 企业版的订单号需要特殊处理
                if tds_i == 1:
                    span_txt = td.find_element_by_css_selector("span").find_element_by_css_selector(
                        "span").find_element_by_css_selector("span")
                    tr_data.append(span_txt.get_attribute("title"))
                else:
                    tr_data.append(td.text)
                tds_i += 1
            data.append(tr_data)

        # 直接传给服务端处理
        api.pull_message(version_types, task_data, order, data)
        return True

    except:
        return False


# 获取二维码并回传数据
def get_login_qrcode(task_data, browser):
    try:

        img_path = "./screenshot/%s%s%s" % (int(time.time()), random.randint(1000, 9999), ".png")
        element = browser.find_element_by_class_name("barcode")
        img_save = element.screenshot(img_path)
        if not img_save:
            return False

        # 打开图片并将其转换为base64
        with open(img_path, 'rb') as img_file:
            base64_data = base64.b64encode(img_file.read()).decode()

        if not base64_data:
            return False

        # 更新任务状态并回传二维码
        api.update_task_order(task_data['task_id'], 2, {"qrcode_data": base64_data})

        # 删除这个图片
        func.remove_file(img_path)

        return True

    except:
        return False
