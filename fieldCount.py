#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/26 下午5:54
# @Author  : Huang HUi
# @Site    : 
# @File    : fieldCount.py
# @Software: PyCharm


import pymysql
import csv
import re
connection = pymysql.connect(host='localhost',
                                 port=3306,
                                 user='root',
                                 db='uniqueway_development',
                                 cursorclass=pymysql.cursors.DictCursor,
                                 charset='utf8')
with connection.cursor() as cursor:
    sql="select * from gen_plan_search_logs where id>28000"
    cursor.execute(sql)
    logss=cursor.fetchall()


count=0
id_count=0
country_ids_count=0
days_count=0
disable_country_ids_count=0
disable_place_ids_count=0
price_count=0
place_ids_count=0
poi_ids_count=0
self_drive_count=0
start_place_id_count=0
finish_place_id_count=0
disable_poi_ids_count=0
hotel_section_count=0
region_ids_count=0
region_ids_days_count=0
tags_count=0
disable_region_ids_count=0
areas_count=0
available_month_count=0
is_in_order_count=0
is_region_only_count=0
for i in logss:
    id=i['id']
    country_ids=i['country_ids']
    days=i['days']
    disable_country_ids=i['disable_country_ids']
    disable_place_ids=i['disable_place_ids']
    max_price=i['max_price']
    min_price=i['min_price']
    place_ids=i['place_ids']
    poi_ids=i['poi_ids']
    self_drive=i['self_drive']
    start_place_id=i['start_place_id']
    finish_place_id=i['finish_place_id']
    disable_poi_ids=i['disable_poi_ids']
    hotel_section=i['hotel_section']
    region_ids=i['region_ids']
    tags=i['tags']
    disable_region_ids=i['disable_region_ids']
    areas=i['areas']
    available_month=i['available_month']
    is_in_order=i['is_in_order']
    is_region_only=i['is_region_only']


    count+=1
    if country_ids!=None:
        country_ids_count+=1
    if days!=None and days!=[4,14]:
        days_count+=1
    if disable_country_ids!=None:
        disable_country_ids_count+=1
    if disable_place_ids!=None:
        disable_place_ids_count+=1
    if max_price!=None and min_price!=None:
        if max_price!=80000 or min_price!=0:
            price_count+=1
    if place_ids!=None:
        place_ids_count+=1
    if poi_ids!=None:
        poi_ids_count+=1
    if self_drive==0 or self_drive==1:
        self_drive_count+=1
    if start_place_id!=None:
        start_place_id_count+=1
    if finish_place_id!=None:
        finish_place_id_count+=1
    if disable_poi_ids!=None:
        disable_poi_ids_count+=1
    if hotel_section!=None:
        hotel_section_count+=1
    if region_ids!=None:
        region_ids_count += 1
        aa=re.findall(r'\"day\"\:\d+',region_ids)
        if aa:
            region_ids_days_count+=1
    if tags!=None:
        tags_count+=1
    if disable_region_ids!=None:
        disable_region_ids_count+=1
    if areas!=None:
        areas_count+=1
    if available_month!=None:
        available_month_count+=1
    if is_in_order==1:
        is_in_order_count+=1
    if is_region_only==1:
        is_region_only_count+=1


with open("gen_plan_search_log_count.csv",'w') as csvout:
    writer=csv.writer(csvout)
    writer.writerow(['Field','Num_count','Percent'])
    writer.writerow(['Count',count,("%.2f")%((count/count)*100)+"%"])
    writer.writerow(['country_ids_count',country_ids_count,("%.2f")%((country_ids_count/count)*100)+"%"])
    writer.writerow(['disable_country_ids_count', disable_country_ids_count, ("%.2f") % ((disable_country_ids_count / count) * 100) + "%"])
    writer.writerow(['days_count', days_count, ("%.2f") % ((days_count / count) * 100) + "%"])
    writer.writerow(['disable_place_ids_count', disable_place_ids_count, ("%.2f") % ((disable_place_ids_count / count) * 100) + "%"])
    writer.writerow(['price_count', price_count, ("%.2f") % ((price_count / count) * 100) + "%"])
    writer.writerow(['place_ids_count', place_ids_count,("%.2f") % ((place_ids_count / count) * 100) + "%"])
    writer.writerow(['poi_ids_count', poi_ids_count, ("%.2f") % ((poi_ids_count / count) * 100) + "%"])
    writer.writerow(['self_drive_count', self_drive_count, ("%.2f") % ((self_drive_count / count) * 100) + "%"])
    writer.writerow(['start_place_id_count', start_place_id_count, ("%.2f") % ((start_place_id_count / count) * 100) + "%"])
    writer.writerow(['finish_place_id_count', finish_place_id_count,("%.2f") % ((finish_place_id_count / count) * 100) + "%"])
    writer.writerow(['disable_poi_ids_count', disable_poi_ids_count, ("%.2f") % ((disable_poi_ids_count / count) * 100) + "%"])
    writer.writerow(['hotel_section_count', hotel_section_count, ("%.2f") % ((hotel_section_count / count) * 100) + "%"])
    writer.writerow(['region_ids_count', region_ids_count, ("%.2f") % ((region_ids_count / count) * 100) + "%"])
    writer.writerow(['region_ids_days_count', region_ids_days_count, ("%.2f") % ((region_ids_days_count / count) * 100) + "%"])
    writer.writerow(['tags_count', tags_count,("%.2f") %((tags_count / count) * 100) + "%"])
    writer.writerow(['disable_region_ids_count', disable_region_ids_count, ("%.2f") % ((disable_region_ids_count / count) * 100) + "%"])
    writer.writerow(['areas_count', areas_count, ("%.2f") % ((areas_count / count) * 100) + "%"])
    writer.writerow(['available_month_count', available_month_count,("%.2f") % ((available_month_count / count) * 100) + "%"])
    writer.writerow(['is_in_order_count', is_in_order_count, ("%.2f") % ((is_in_order_count / count) * 100) + "%"])
    writer.writerow(['is_region_only_count', is_region_only_count, ("%.2f") % ((is_region_only_count / count) * 100) + "%"])

print("country_ids_percent                ",country_ids_count,'    ',("%.2f")%((country_ids_count/count)*100)+"%")
print("days_count_percent                 ",days_count,'    ',("%.2f")%((days_count/count)*100)+"%")
print("disable_country_ids_percent        ",disable_country_ids_count,'    ',("%.2f")%(disable_country_ids_count/count))
print("disable_place_ids_percent          ",disable_place_ids_count,'    ',("%.2f")%(disable_place_ids_count/count))
print("price_percent                      ",price_count,'    ',("%.2f")%(price_count/count))
print("place_ids_count_percent            ",place_ids_count,'    ',("%.2f")%(place_ids_count/count))
print("poi_ids_count_percent              ",poi_ids_count,'    ',("%.2f")%(poi_ids_count/count))
print("self_drive_count_percent           ",self_drive_count,'    ',("%.2f")%(self_drive_count/count))
print("start_place_id_count_percent       ",start_place_id_count,'    ',("%.2f")%(start_place_id_count/count))
print("finish_place_id_count_percent      ",finish_place_id_count,'    ',("%.2f")%(finish_place_id_count/count))
print("disable_poi_ids_count_percent      ",disable_poi_ids_count,'    ',("%.2f")%(disable_poi_ids_count/count))
print("hotel_section_count_percent        ",hotel_section_count,'    ',("%.2f")%(hotel_section_count/count))
print("region_ids_count_percent           ",region_ids_count,'    ',("%.2f")%(region_ids_count/count))
print("tags_count_percent                 ",tags_count,'    ',("%.2f")%(tags_count/count))
print("disable_region_ids_count_percent   ",disable_region_ids_count,'    ',("%.2f")%(disable_region_ids_count/count))
print("areas_count_percent                ",areas_count,'    ',("%.2f")%(areas_count/count))
print("available_month_count_percent      ",available_month_count,'    ',("%.2f")%(available_month_count/count))
print("is_in_order_count_percent          ",is_in_order_count,'    ',("%.2f")%(is_in_order_count/count))
print("is_region_only_count_percent       ",is_region_only_count,'    ',("%.2f")%(is_region_only_count/count))





