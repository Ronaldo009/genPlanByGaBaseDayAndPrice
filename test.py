#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 上午11:50
# @Author  : Huang HUi
# @Site    : 
# @File    : test.py
# @Software: PyCharm
import random
GIVEN_QUERY = {'days': [4,14], 'countries': [{'country_id': 28, 'day': None}],
    'regions': [{'region_id': 2, 'day': None}, {'region_id': 27, 'day': 1}, {'region_id': 69, 'day': None}], 'pois': [],
    'regionNotGo': [], 'poiNotGo': [], 'regionSorted': [135, 131], 'availableMonths': [1,2,3,4,5,6,7,8,9,10],
    'price': [0, 80000], 'hotelRating': None, 'arrivalRegionId': None, 'departRegionId': None}

aa=[{'region_id': 2, 'days': 2}, {'region_id': 27, 'days': 1}, {'region_id': 69, 'days': 1}, {'region_id': 3, 'days': 1}]

regionsMapInGenPlan = {x['region_id']: x['days'] for x in aa}

countryIds = list(map(lambda x: x['country_id'], GIVEN_QUERY['countries']))
days=GIVEN_QUERY['days']
regions=GIVEN_QUERY['regions']
regionDic=list(map(lambda x:{x['region_id']:x['day']},regions))
bb=[2,3,4,5]
regionsMapInQuery = {x['region_id']: x['day'] for x in regions}

aa=dict(a=3)
if (set(regionsMapInQuery.keys()) - set(regionsMapInGenPlan.keys())):
    print("ssssss")

print(regionsMapInQuery.items())
print(regionsMapInGenPlan.items())

a=[1,2,0,4,5]
b=[11,22,33,44]
c=99
f=[]
g=[]
flag=True
while flag:
    try:
        flag=False

        f.append(c/a[1])
    except:
        print("ass")
        flag=True
print(f)

cc=7
if cc<10:
    k=1
elif cc<8:
