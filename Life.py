#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 上午11:34
# @Author  : Huang HUi
# @Site    : 
# @File    : Life.py
# @Software: PyCharm

SCORE_NONE = 0.00001

class Life(object):
      """个体类"""
      def __init__(self, aGene = None):
            self.gene = aGene
            self.scoreDays = SCORE_NONE
            self.scorePrices = SCORE_NONE


