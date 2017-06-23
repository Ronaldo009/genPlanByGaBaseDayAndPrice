#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 上午11:41
# @Author  : Huang HUi
# @Site    : 
# @File    : mysqlConnection.py
# @Software: PyCharm
import pymysql.cursors

def onlineConnection():
    connection = pymysql.connect(host='192.168.100.253',
                                 port=3306,
                                 user='unireader',
                                 password='7LWFu(RMYHKb>dWvM6gEE(GKFWwhL',
                                 db='uniqueway_production',
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

def localConnection():
    connection = pymysql.connect(host='localhost',
                                 port=3306,
                                 user='root',
                                 db='uniqueway_development',
                                 cursorclass=pymysql.cursors.DictCursor,
                                 charset='utf8')

    return connection

def mysqlConnection():
    connection = localConnection()
    # connection = onlineConnection()
    return connection

