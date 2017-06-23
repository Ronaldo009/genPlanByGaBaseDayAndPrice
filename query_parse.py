#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/20 下午4:00
# @Author  : Huang HUi
# @Site    : 
# @File    : query_parse.py
# @Software: PyCharm
from mysqlConnection import mysqlConnection
import yaml
import copy
import time


GIVEN_QUERY = {'days': [10,12,13,14], 'countries': [{'country_id': 28, 'day': None}],
    'regions': [{'region_id': 2, 'day': None}, {'region_id': 27, 'day': None}, {'region_id': 69, 'day': None}], 'pois': [],
    'regionNotGo': [], 'poiNotGo': [], 'regionSorted': [135, 131], 'availableMonths': [1,2,3,4,5,6,7,8,9,10],
    'price': [0, 80000], 'hotelRating': None, 'arrivalRegionId': 27, 'departRegionId': None}

# GIVEN_QUERY={'days': [10], 'countries': [{'country_id': 11, 'day': None}], 'regions': [{'region_id': 266, 'day': None},
#         {'region_id': 220, 'day': None}, {'region_id': 2141}], 'pois': [795, 800, 878, 1536, 1679, 2400, 2502, 3472, 7305, 13850, 14817, 15390, 15582, 16848]}

# GIVEN_QUERY={'days': [12], 'countries': [{'country_id': 28, 'day': None}],
#              'regions': [{'region_id': 2, 'day': None}, {'region_id': 70, 'day': None}, {'region_id': 69, 'day': None}, {'region_id': 27, 'day': None}, {'region_id': 79, 'day': None}],
#              'pois': [1361, 1380, 1382, 1385, 1386, 1413, 1512, 1700, 1701, 1712, 1713, 1934, 2051, 2064, 2065, 2066, 2080, 2156, 2682, 2917, 4119, 6443, 6946, 6968, 8797, 8802, 9500, 9511, 9514, 9526, 9545, 12893, 14580, 14748, 15773, 16847, 16916, 17000, 17677, 18551, 22330, 28186, 28236]}

try:
    countryIds_query = list(map(lambda x: x['country_id'], GIVEN_QUERY['countries']))
except :
    countryIds_query=None
try:
    days_query=GIVEN_QUERY['days']
except :
    days_query=None
try:
    regions_query = GIVEN_QUERY['regions']
except :
    regions_query=None
try:
    regionDic_query = list(map(lambda x: {x['region_id']: x['day']}, regions_query))
except :
    regionDic_query=None
try:
    pois_query=GIVEN_QUERY['pois']
except :
    pois_query=None
try:
    regionNotGo_query=GIVEN_QUERY['regionNotGo']
except :
    regionNotGo_query=None
try:
    poiNotGo_query=GIVEN_QUERY['poiNotGo']
except :
    poiNotGo_query=None
try:
    regionSorted_query=GIVEN_QUERY['regionSorted']
except :
    regionSorted_query=None
try:
    availableMonths_query=GIVEN_QUERY['availableMonths']
except :
    availableMonths_query=None
try:
    price_query=GIVEN_QUERY['price']
except :
    price_query=None
try:
    hotelRating_query=GIVEN_QUERY['hotelRating']
except :
    hotelRating_query=None
try:
    arrivalRegionId_query=GIVEN_QUERY['arrivalRegionId']
except :
    arrivalRegionId_query=None
try:
    departRegionId_query=GIVEN_QUERY['departRegionId']
except:
    departRegionId_query=None




start2=time.clock()
connection=mysqlConnection()
try:
    with connection.cursor() as cursor:
        sql = "SELECT tidy_parts.id, parts2.id AS next_id FROM tidy_parts ,tidy_parts AS parts2 WHERE tidy_parts.deleted_at is null and parts2.deleted_at is null and tidy_parts.tail_place_id = parts2.prev_place_id AND tidy_parts.next_place_id = parts2.head_place_id and tidy_parts.tail = parts2.head and tidy_parts.departure_transit = parts2.arrive_transit and tidy_parts.state != 'canceled' and parts2.state != 'canceled' AND timestampdiff(SECOND, tidy_parts.end_time,parts2.start_time) < 7201 and timestampdiff(SECOND, tidy_parts.end_time,parts2.start_time) >= 0;"
        cursor.execute(sql)
        partPairs = cursor.fetchall()
        if GIVEN_QUERY['countries']:
            # country condition
            if arrivalRegionId_query:
                sql = "SELECT tidy_parts.id as id, country_id,region_id FROM tidy_parts join regions on tidy_parts.region_id = regions.id WHERE tidy_parts.is_start = 1 and tidy_parts.poi_ids is not NULL and tidy_parts.state!='canceled' and tidy_parts.deleted_at is null and region_id =(%s) and country_id in (%s)" % (arrivalRegionId_query,str(countryIds_query)[1:-1])
            else:
                sql = "SELECT tidy_parts.id as id, country_id FROM tidy_parts join regions on tidy_parts.region_id = regions.id WHERE tidy_parts.is_start = 1 and tidy_parts.poi_ids is not NULL and tidy_parts.state!='canceled' and tidy_parts.deleted_at is null and country_id in (%s)" % str(countryIds_query)[1:-1]
        else:
            # all
            sql = "SELECT id FROM tidy_parts WHERE tidy_parts.is_start = 1 and tidy_parts.poi_ids is not NULL and tidy_parts.state!='canceled' and tidy_parts.deleted_at is null "
        cursor.execute(sql)
        startParts = cursor.fetchall()
        if departRegionId_query:
            sql = "SELECT id ,region_id FROM tidy_parts WHERE tidy_parts.is_end = 1 and region_id= (%s)"%(departRegionId_query)

        sql = "SELECT id FROM tidy_parts WHERE tidy_parts.is_end = 1 "
        cursor.execute(sql)
        endParts = cursor.fetchall()
        sql = "SELECT id,poi_ids,start_time, end_time, days, head_place_id, tail_place_id, place_id, destination_id, plan_id, planner_id, self_drive, tail, head, schedules, next_place_id, prev_place_id from tidy_parts where poi_ids is not NULL and state!='canceled' and deleted_at is null "  # WHERE tidy_parts.id in (174,175,176,177,180,181,182,187,188,189,190,191,192,193,194,195,196,201,202,203,204,205,206,207,209,210,211,212,217,218,219,220,221,222,224,225,226,227,228,229,230,261,262,263,264,265,266,267,268,269,270,271,272,273,274,294,295,296,297,298,299,301,303,304,315,325,328,329,330,331,332,335,344,345,346,347,349,350,351,352,353)"
        cursor.execute(sql)
        partRecords = cursor.fetchall()
        sql = "SELECT id, price_number, rating, category, is_feature, is_prepaid, price, country_id, is_forbid, type, rental_company, arrival_poi_id, transport_method, terminal_station_id ,longitude, latitude, place_id ,name ,display_name , currency_id FROM pois"
        cursor.execute(sql)
        poiRecords = cursor.fetchall()
        sql = "SELECT id, planner_id FROM plans"
        cursor.execute(sql)
        planRecords = cursor.fetchall()
        sql = "SELECT id, poi_id, times ,cross_days, start_time, end_time FROM tidy_schedule_pois"
        cursor.execute(sql)
        schedulePoiRecords = cursor.fetchall()
        sql = "SELECT id, country_id, region_id, name FROM places"
        cursor.execute(sql)
        placeRecords = cursor.fetchall()
        sql = "SELECT id, name FROM regions"
        cursor.execute(sql)
        regionRecords = cursor.fetchall()
        sql = "SELECT id, name FROM countries"
        cursor.execute(sql)
        countryRecords = cursor.fetchall()
        sql = "SELECT id, place_id FROM tidy_schedule_places"
        cursor.execute(sql)
        schedulePlaceRecords = cursor.fetchall()
        sql = "SELECT name, taggable_id as id FROM tags WHERE taggable_type = 'Poi'"
        cursor.execute(sql)
        poiTagsRecords = cursor.fetchall()
        sql = "SELECT id, abbreviation, rate FROM currencies"
        cursor.execute(sql)
        currencyRecords = cursor.fetchall()
        sql = "SELECT distinct(poi_id) as id , month(date) as month FROM poi_calendars WHERE state in (\"available\",\"part_available\")"
        cursor.execute(sql)
        poiCalendarRecords = cursor.fetchall()
        sql = "SELECT id, name from gen_plan_tags"
        cursor.execute(sql)
        tagsIdRecords = cursor.fetchall()

        end2=time.clock()
        runtime2=end2-start2
        print("----------------mysql读取完成,用时"+str(("%.2f")%(runtime2))+"秒------------------")

finally:
    connection.close()
# get the next parts dictionary { current_part_id => [next_part_ids]} ,
# here the available next parts satisfy:
# current_part.place_id = next_part.prev_place_id, current_part.next_place_id = next_part.place_id
start3=time.clock()
parts = {}
for record in partRecords:
    # print(record['id'])
    parts[record['id']] = record
    if parts[record['id']]['poi_ids'] != None:
        parts[record['id']]['poi_ids'] = yaml.load(parts[record['id']]['poi_ids'])
    else:
        parts[record['id']]['poi_ids'] = []
    parts[record['id']].pop('id')

if not partRecords:
    raise ImportError("import")

nextPartsOf = {}
for idPair in partPairs:
    if idPair['id'] in nextPartsOf:
        nextPartsOf[idPair['id']].append(idPair['next_id'])
    else:
        nextPartsOf[idPair['id']] = [idPair['next_id']]

prevPartsOf={}
for idPair in partPairs:
    if idPair['next_id'] in prevPartsOf:
        prevPartsOf[idPair['next_id']].append(idPair['id'])
    else:
        prevPartsOf[idPair['next_id']]=[idPair['id']]

subParts = {}
for part in parts:
    if part in nextPartsOf:
        subParts[part] = nextPartsOf[part]
    else:
        subParts[part] = []


schedulePois = {}
for record in schedulePoiRecords:
    schedulePois[record['id']] = record
    schedulePois[record['id']].pop('id')

pois = {}
placePoisMapping = {}
for record in poiRecords:
    pois[record['id']] = record
    if record['place_id'] in placePoisMapping:
        placePoisMapping[record['place_id']].append(copy.deepcopy(record))
    else:
        placePoisMapping[record['place_id']] = [copy.deepcopy(record)]
    pois[record['id']].pop('id')


planers = {}
for record in planRecords:
    planers[record['id']] = record['planner_id']

startParts = [dict['id'] for dict in startParts]




endParts = [dict['id'] for dict in endParts]

places = {}
for record in placeRecords:
    places[record['id']] = record
    places[record['id']].pop('id')

regions = {}
for record in regionRecords:
    regions[record['id']] = record
    regions[record['id']].pop('id')

countries = {}
for record in countryRecords:
    countries[record['id']] = record
    countries[record['id']].pop('id')

schedulePlaces = {}
for record in schedulePlaceRecords:
    schedulePlaces[record['id']] = record
    schedulePlaces[record['id']].pop('id')

poiTags = {}
for record in poiTagsRecords:
    if record['id'] in poiTags:
        poiTags[record['id']].append(record['name'])
    else:
        poiTags[record['id']] = [record['name']]

currencies = {}
for record in currencyRecords:
    currencies[record['id']] = record
    currencies[record['id']].pop('id')

poiCalendar = {}
for record in poiCalendarRecords:
    if record['id'] in poiCalendar:
        poiCalendar[record['id']].append(record['month'])
    else:
        poiCalendar[record['id']] = [record['month']]

tagsId = {}
for record in tagsIdRecords:
    if record['name'] not in tagsId:
        tagsId[record['name']] = record['id']
end3=time.clock()
runtime3=end3-start3


print("----------------生成字典完成,用时"+str(("%.2f")%(runtime3))+"秒------------------")
