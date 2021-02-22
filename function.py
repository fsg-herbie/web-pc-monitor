#!/usr/bin/python3
# -*- coding: utf-8 -*-

import platform
import requests
import json
import socket
import uuid
import string
import zipfile
import os


# 获取当前目录
def get_base_path():
    return os.getcwd()


# 获取系统类型
def get_sys_platform():
    return platform.system()


def get_hostname():
    return socket.gethostname()


def get_ip_address():
    return socket.gethostbyname(get_hostname())


def get_ip_httpbin():
    response = requests.get("http://httpbin.org/ip")
    ip = json.loads(response.text)
    if not ip:
        return False
    return ip.origin


# 获取MAC
def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


def remove_file(file):
    if os.path.exists(file):
        os.remove(file)
        return True
    else:
        return False


# 访问API
def curl(url, types="get", param=None):
    headers = {'Key': 'zdsCnjuH7Z2CtjxMRjfqktiDl9slni/WCYBrNe8sfjjsdhHGIHGu', "Accept-Encoding": "Gzip"}

    # 设置一个超时重连定时器 最大3次
    i = 0
    while i < 3:

        if i >= 3:
            return False

        try:
            if types == "get":
                result = requests.get(url, timeout=(15, 10), headers=headers, json=param)
            else:
                result = requests.post(url, timeout=(15, 10), headers=headers, json=param)

            result.raise_for_status()
            result.encoding = result.apparent_encoding

            # 将json转换为字典
            return json.loads(result.text)
        except:
            print("请求 %s 超时了 %s 次,请求参数：%s" % (url, i+1, param))
            i += 1


# 创建代理用户名和密码认证插件
def create_proxyauth_extension(proxy_host, proxy_port, proxy_username, proxy_password, scheme='http', plugin_path=None):

    if plugin_path is None:
        plugin_path = 'chrome_proxyauth_plugin.zip'

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",   
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
        """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "${scheme}",
                host: "${host}",
                port: parseInt(${port})
              },
              bypassList: ["foobar.com"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "${username}",
                password: "${password}"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path
