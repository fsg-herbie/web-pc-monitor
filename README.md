# alipay-pc-monitor 某宝PC账单监控程序
本程序基于python3 selenium框架开发的一套收款账单监控
支持Linux、MAC、Windows，需要对selenium webdriver有一定了解

运行需要google浏览器和chromedriver插件驱动，而且需要对应谷歌浏览器版本号，不然会报错，本源码的webdriver目录有对应系统的插件，但是有两年没用了，我记得之前应该是85.04版本
当然也可以自己到 http://npm.taobao.org/mirrors/chromedriver 下载最新版本对应最新的google浏览器

这是我之前做的一个项目，跟后端接口结合而开发的一套监控某宝网页支付账单的爬虫程序,支持多线程多任务监控

里面集成了接口接受数据，自动刷新网页，模拟人工点击等技术要领

使用前请先阅读 api.py 文件的方法，先跟后端接口结合，后端分发任务给main.py，然后python会启动一个监听浏览器的窗口和把获取的数据传输给后端，可分发多个任务，最终能开多少个取决于系统的配置。

本程序只供爬虫学习研究使用，严禁用于非法用途。
