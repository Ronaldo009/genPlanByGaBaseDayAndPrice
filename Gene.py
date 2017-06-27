#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/23 上午10:36
# @Author  : Huang HUi
# @Site    : 
# @File    : Gene.py
# @Software: PyCharm

class Gene(object):
    def __init__(self,Id,day,price):
        self.part=Id
        self.day=day
        self.price=price