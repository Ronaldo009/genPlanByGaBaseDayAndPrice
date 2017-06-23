#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 下午2:17
# @Author  : Huang HUi
# @Site    : 
# @File    : genPlanConstraint.py
# @Software: PyCharm

from datetime import timedelta
from datetime import datetime
import argparse
import json
import yaml
import copy
import itertools
import random
from GA import GA
from collections import  Counter,OrderedDict
import ast
import hashlib
import itertools
import re

from geopy.distance import great_circle
from functools import reduce
import base64

from random import sample

def extractSchedulesFromPart(part,broadParts):
    decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
    orderedDict = decoder.decode(broadParts[part]['schedules'])
    return orderedDict

def mergeSchedules(order,broadParts):
    schedules=OrderedDict({})
    lastPart=None
    lastScheduleId=None
    for part in order:
        couldMerge=False
        if lastPart:
            couldMerge = broadParts[lastPart]["tail"] == "incomplete" and broadParts[part]["head"] == "incomplete"
        for schedule, schedulePlace in extractSchedulesFromPart(part,broadParts).items():
            if couldMerge:
                schedules[lastScheduleId].update(schedulePlace)
                couldMerge = False
            else:
                if schedule in schedules:
                    schedules["0" + schedule] = schedulePlace
                else:
                    schedules[schedule] = schedulePlace
                lastScheduleId = schedule
        lastPart = part
    return schedules


def getKeyFromStrDict(strDict):
    keyTurn = True
    valueTurn = False
    scheduleArray = []
    key = ""
    value = ""
    appended = False
    firstLayer = True
    for s in strDict[1:-1]:
        if s == '{':
            firstLayer = False
            continue
        if s == "}":
            firstLayer = True
            continue
        if not firstLayer:
            continue
        if s == ":":
            keyTurn = False
            valueTurn = True
            scheduleArray.append(ast.literal_eval(key))
            appended = True
            key = ""
            continue
        if s == ",":
            keyTurn = True
            valueTurn = False
            appended = False
            continue
        if keyTurn:
            key += s
            continue
        if valueTurn and not appended:
            continue
    return scheduleArray

def calculatePoiPrice(poi, broadPois, broadCurrencies):
    if float(broadPois[poi]['price_number']) == 0 or broadPois[poi]['price_number'] == None:
        return 0.0, "None"
    price = float(broadPois[poi]['price_number']) * float(broadCurrencies[broadPois[poi]['currency_id']]['rate'])
    currency = broadCurrencies[broadPois[poi]['currency_id']]['abbreviation']
    return price, currency
def everyTwo(_list):
    return list(zip(_list[::2], _list[1::2]))
def getCarRentingCost(realSchedule, broadPois, broadSchedulePois, broadCurrencies):
    totalCost = 0.0
    schePoisTempList = re.findall(r'\[[\d,]+\]',realSchedule)
    schePois = ast.literal_eval('[' + ''.join(re.findall(r'[\d,]+', str(schePoisTempList))) + ']')
    carRentSchePois = list(filter(lambda sPoi: broadPois[broadSchedulePois[sPoi]['poi_id']]['type'] == 'Pois::CarRental', schePois))
    SchCarRentPoiDetails = []
    if len(carRentSchePois) % 2 != 0:
        raise IOError("租车schpoi不是偶数")
    else:
        for pair in everyTwo(carRentSchePois):
            reg_for_getting_days = str(pair[0]) + '.+' + str(pair[1])
            schedules_snippet = re.findall(re.compile(reg_for_getting_days),realSchedule)
            # if the sum of start renting time and end renting time is less than 24 hours, then it counts day 1, else if it is more than 24 hours, it counts day 2
            if broadSchedulePois[pair[0]]['start_time'] + broadSchedulePois[pair[1]]['end_time'] < timedelta(days= 1):
                days_addon = 0
            else:
                days_addon = 1
            days = len(re.findall(r'\d+\":{',schedules_snippet[0])) + days_addon
            price_number0, currency0 = calculatePoiPrice(broadSchedulePois[pair[0]]['poi_id'], broadPois, broadCurrencies)
            SchCarRentPoiDetails.append({"sch_poi_id": pair[0],
                                         "price_number": price_number0,
                                         "days": days,
                                         "type": 'Pois::CarRental',
                                         "is_prepaid": broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"]
                                         # "currency": currency0
                                         })
            price_number1, currency1 = calculatePoiPrice(broadSchedulePois[pair[1]]['poi_id'], broadPois, broadCurrencies)
            SchCarRentPoiDetails.append({"sch_poi_id": pair[1],
                                         "price_number": price_number1,
                                         "days": 0,
                                         "type": 'Pois::CarRental',
                                         "is_prepaid":broadPois[broadSchedulePois[pair[1]]['poi_id']]["is_prepaid"]
                                         # "currency": currency1
                                         })
            if broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"] == 1:
                totalCost += float(broadPois[broadSchedulePois[pair[0]]['poi_id']]['price_number']) * float(days)
    return totalCost, SchCarRentPoiDetails
def getRealSchedule(path, broadParts):
    return broadParts[path[0]]['schedules'] + ''.join(map(lambda x :re.sub(r'{\"\d+\":{',',', broadParts[x]['schedules']), path[1:]))

def everyTwoWithOverLap(_list):
    return list(zip(_list[::1], _list[1::1]))

def getHotelCost(realSchedule, broadPois, broadSchedulePois, broadPlacePoisMapping, broadCurrencies):
    totalCost = 0.0
    totalDays = 0
    schePoisTempList = re.findall(r'\[[\d,]+\]', realSchedule)
    schePois = ast.literal_eval('[' + ''.join(re.findall(r'[\d,]+', str(schePoisTempList))) + ']')
    hotelAndCrossDaySchePois = list(
        filter(lambda sPoi: broadPois[broadSchedulePois[sPoi]['poi_id']]['type'] == 'Pois::Hotel' or (broadSchedulePois[sPoi]['cross_days'] and broadSchedulePois[sPoi]['cross_days'] > 0), schePois))

    schHotelPoiDetails = []
    # current_day aims to count current hotel occupy which days, like hotel B lives in day 3, day 4
    current_day = 1

    for pair in everyTwoWithOverLap(hotelAndCrossDaySchePois + ['END']):  # END is a flag in order to iter the last one, because every iter, we use pair[0]
        #print("pair is:", pair)
        # HERE USE REGEX TO GET THE RIGHT SCH POI, IT MUST SATISFY STARTING WITH '[' OR ',' ,ENDING WITH ',' OR ']', STARTING WITHOUT '"','NUMBER' ,ENDIND WITHOUT '"','NUMBER'
        reg_for_getting_days = "(?<=[\,\[])(?<![\"\d])" + str(pair[0]) + "(?=[\,\]])(?![\d\"])" + '.+' + "(?<![\"\d])(?<=[\,\[])" + str(pair[1]) + "(?![\d\"])(?=[\,\]])"
        #print(reg_for_getting_days)
        schedules_snippet = re.findall(re.compile(reg_for_getting_days), realSchedule + "[END]")
        # if len(schedules_snippet) == 0:
        #     print(realSchedule,reg_for_getting_days)

        days = len(re.findall(r'\d+\":{', schedules_snippet[0]))


        if broadPois[broadSchedulePois[pair[0]]['poi_id']]['type'] == 'Pois::Hotel':
            price_number, currency = calculatePoiPrice(broadSchedulePois[pair[0]]['poi_id'], broadPois, broadCurrencies)
            schHotelPoiDetails.append({"sch_poi_id": pair[0],
                                       "price_number": price_number,
                                       "days": days,
                                       "start_day":current_day,
                                       "type": 'Pois::Hotel',
                                       "is_prepaid": broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"]
                                       # "currency": currency
                                       })
            if broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"] == 1:
                totalCost += float(broadPois[broadSchedulePois[pair[0]]['poi_id']]['price_number']) * float(days)
                totalDays += days
        current_day += days
    return totalCost, totalDays, schHotelPoiDetails
def getTourRegionsFromSchedules(schedules, broadSchedulePois, broadPois, broadSchedulePlaces, broadPlaces):
    tourRegions = []
    # here we assume that there are no two same places with different schedule_place_id in one day
    for schedule, schedule_places in schedules.items():
        todayTourRegions = []
        # if debug:
        #     print("schedule", schedule, "-> ", schedule_places)
        for schedule_place, pois in schedule_places.items():
            # print("schedule_place:", schedule_place, "pois: ", pois)
            for poi in pois:
                ## TODO here need a definition of tour places!
                if broadPois[broadSchedulePois[int(poi)]['poi_id']]['type'] in ['Pois::Attraction', 'Pois::Activity',]:
                    region_id = broadPlaces[broadSchedulePlaces[int(schedule_place)]['place_id']]['region_id']
                    #print("poi_id: ", broadSchedulePois[int(poi)]['poi_id'],broadPois[broadSchedulePois[int(poi)]['poi_id']])
                    #print("schedule poi_id: " ,int(poi))
                    #print("region_id: ", region_id)
                    # if debug:
                    #     print("schedule_place",  schedule_place, "place_id",broadSchedulePlaces[int(schedule_place)]['place_id'], "region_id", region_id)
                    if region_id:
                        # if debug:
                        #     print("region", region_id, " schedule_place -> ", schedule_place)
                        todayTourRegions.append(broadPlaces[broadSchedulePlaces[int(schedule_place)]['place_id']]['region_id'])
                    break
        #print("today regions:", todayTourRegions)

        tourRegions += todayTourRegions
        # if debug:
        #     print(tourRegions)
    return tourRegions
def compress(placesOrRegions):
    newPlaceOrRegion = []
    for placeOrRegion in placesOrRegions:
        if not newPlaceOrRegion or newPlaceOrRegion[-1] != placeOrRegion:
            newPlaceOrRegion.append(placeOrRegion)
    return newPlaceOrRegion

def getPlacesFromSchedules(schedules):
    return map(lambda x: int(x[0:-3]), re.findall(r'\d+\"\:\[',schedules))

def getFirstNonTipPoiRaw(part,broadParts,broadPois):
    partPois = broadParts[part]['poi_ids']
    for poi in partPois:
        if broadPois[poi]['type'] != 'Pois::Tip':
            return poi

def getLastNonTipPoiRaw(part,broadParts,broadPois):
    partPois = broadParts[part]['poi_ids']
    for poi in reversed(partPois):
        if broadPois[poi]['type'] != 'Pois::Tip':
            return poi

def station_constraint(prevPart, part, broadPois, broadParts):
    departurePoi = broadPois[getLastNonTipPoiRaw(prevPart, broadParts=broadParts, broadPois=broadPois)]
    currentPoiId = getFirstNonTipPoiRaw(part, broadParts=broadParts, broadPois=broadPois)
    ## 针对美国和加拿大 不加station 限制
    if departurePoi['type'] == 'Pois::Flight' and departurePoi['country_id'] in [11,27]:
        return True
    if departurePoi['type'] == 'Pois::Flight' and departurePoi['arrival_poi_id'] != currentPoiId:
        return False
    elif departurePoi['transport_method'] in ['火车', '轮渡', '缆车', '地铁'] and departurePoi['terminal_station_id'] != currentPoiId:
        return False
    elif broadParts[prevPart]['next_place_id'] != broadParts[part]['head_place_id']:
        return False
    return True


def Id(path):
    """
    MD5加密算法
    :param path:
    :return:
    """
    m = hashlib.md5()
    m.update(str(path).encode('utf-8'))
    return m.hexdigest()
def getTourPlacesFromSchedules(schedules, broadSchedulePois, broadPois, broadSchedulePlaces):
    tourPlaces = []
    # here we assume that there are no two same places with different schedule_place_id in one day
    for schedule, schedule_places in schedules.items():
        todayTourPlaces = []
        for schedule_place, pois in schedule_places.items():
            for poi in pois:
                ## TODO here need a definition of tour places!
                if broadPois[broadSchedulePois[int(poi)]['poi_id']]['type'] in ['Pois::Attraction', 'Pois::Activity']:
                    todayTourPlaces.append(broadSchedulePlaces[int(schedule_place)]['place_id'])
                    break
        tourPlaces += todayTourPlaces
    return tourPlaces

def getFirstAndLastSchAirportPoi(first_schdule, last_schedule, broadSchedulePois, broadPois):
    first_and_last_schdule_pois = itertools.chain.from_iterable(map(lambda x: ast.literal_eval(x), re.findall(r'\[[\d,]+\]', first_schdule + last_schedule)))
    airport_pois = list(filter(lambda x: broadPois[broadSchedulePois[x]['poi_id']]['type'] == 'Pois::Airport', first_and_last_schdule_pois))
    if len(airport_pois) > 0:
        return airport_pois[0], airport_pois[-1]
    else:
        return None, None




def extractSchedulesFromPart(part,broadParts):
    decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
    orderedDict = decoder.decode(broadParts[part]['schedules'])
    return orderedDict

def mergeSchedules(order,broadParts):
    schedules=OrderedDict({})
    lastPart=None
    lastScheduleId=None
    for part in order:
        couldMerge=False
        if lastPart:
            couldMerge = broadParts[lastPart]["tail"] == "incomplete" and broadParts[part]["head"] == "incomplete"
        for schedule, schedulePlace in extractSchedulesFromPart(part,broadParts).items():
            if couldMerge:
                schedules[lastScheduleId].update(schedulePlace)
                couldMerge = False
            else:
                if schedule in schedules:
                    schedules["0" + schedule] = schedulePlace
                else:
                    schedules[schedule] = schedulePlace
                lastScheduleId = schedule
        lastPart = part
    return schedules


def getKeyFromStrDict(strDict):
    keyTurn = True
    valueTurn = False
    scheduleArray = []
    key = ""
    value = ""
    appended = False
    firstLayer = True
    for s in strDict[1:-1]:
        if s == '{':
            firstLayer = False
            continue
        if s == "}":
            firstLayer = True
            continue
        if not firstLayer:
            continue
        if s == ":":
            keyTurn = False
            valueTurn = True
            scheduleArray.append(ast.literal_eval(key))
            appended = True
            key = ""
            continue
        if s == ",":
            keyTurn = True
            valueTurn = False
            appended = False
            continue
        if keyTurn:
            key += s
            continue
        if valueTurn and not appended:
            continue
    return scheduleArray

def calculatePoiPrice(poi, broadPois, broadCurrencies):
    if float(broadPois[poi]['price_number']) == 0 or broadPois[poi]['price_number'] == None:
        return 0.0, "None"
    price = float(broadPois[poi]['price_number']) * float(broadCurrencies[broadPois[poi]['currency_id']]['rate'])
    currency = broadCurrencies[broadPois[poi]['currency_id']]['abbreviation']
    return price, currency
def everyTwo(_list):
    return list(zip(_list[::2], _list[1::2]))
def getCarRentingCost(realSchedule, broadPois, broadSchedulePois, broadCurrencies):
    totalCost = 0.0
    schePoisTempList = re.findall(r'\[[\d,]+\]',realSchedule)
    schePois = ast.literal_eval('[' + ''.join(re.findall(r'[\d,]+', str(schePoisTempList))) + ']')
    carRentSchePois = list(filter(lambda sPoi: broadPois[broadSchedulePois[sPoi]['poi_id']]['type'] == 'Pois::CarRental', schePois))
    SchCarRentPoiDetails = []
    if len(carRentSchePois) % 2 != 0:
        raise IOError("租车schpoi不是偶数")
    else:
        for pair in everyTwo(carRentSchePois):
            reg_for_getting_days = str(pair[0]) + '.+' + str(pair[1])
            schedules_snippet = re.findall(re.compile(reg_for_getting_days),realSchedule)
            # if the sum of start renting time and end renting time is less than 24 hours, then it counts day 1, else if it is more than 24 hours, it counts day 2
            if broadSchedulePois[pair[0]]['start_time'] + broadSchedulePois[pair[1]]['end_time'] < timedelta(days= 1):
                days_addon = 0
            else:
                days_addon = 1
            days = len(re.findall(r'\d+\":{',schedules_snippet[0])) + days_addon
            price_number0, currency0 = calculatePoiPrice(broadSchedulePois[pair[0]]['poi_id'], broadPois, broadCurrencies)
            SchCarRentPoiDetails.append({"sch_poi_id": pair[0],
                                         "price_number": price_number0,
                                         "days": days,
                                         "type": 'Pois::CarRental',
                                         "is_prepaid": broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"]
                                         # "currency": currency0
                                         })
            price_number1, currency1 = calculatePoiPrice(broadSchedulePois[pair[1]]['poi_id'], broadPois, broadCurrencies)
            SchCarRentPoiDetails.append({"sch_poi_id": pair[1],
                                         "price_number": price_number1,
                                         "days": 0,
                                         "type": 'Pois::CarRental',
                                         "is_prepaid":broadPois[broadSchedulePois[pair[1]]['poi_id']]["is_prepaid"]
                                         # "currency": currency1
                                         })
            if broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"] == 1:
                totalCost += float(broadPois[broadSchedulePois[pair[0]]['poi_id']]['price_number']) * float(days)
    return totalCost, SchCarRentPoiDetails
def getRealSchedule(path, broadParts):
    return broadParts[path[0]]['schedules'] + ''.join(map(lambda x :re.sub(r'{\"\d+\":{',',', broadParts[x]['schedules']), path[1:]))

def everyTwoWithOverLap(_list):
    return list(zip(_list[::1], _list[1::1]))

def getHotelCost(realSchedule, broadPois, broadSchedulePois, broadPlacePoisMapping, broadCurrencies):
    totalCost = 0.0
    totalDays = 0
    schePoisTempList = re.findall(r'\[[\d,]+\]', realSchedule)
    schePois = ast.literal_eval('[' + ''.join(re.findall(r'[\d,]+', str(schePoisTempList))) + ']')
    hotelAndCrossDaySchePois = list(
        filter(lambda sPoi: broadPois[broadSchedulePois[sPoi]['poi_id']]['type'] == 'Pois::Hotel' or (broadSchedulePois[sPoi]['cross_days'] and broadSchedulePois[sPoi]['cross_days'] > 0), schePois))

    schHotelPoiDetails = []
    # current_day aims to count current hotel occupy which days, like hotel B lives in day 3, day 4
    current_day = 1

    for pair in everyTwoWithOverLap(hotelAndCrossDaySchePois + ['END']):  # END is a flag in order to iter the last one, because every iter, we use pair[0]
        #print("pair is:", pair)
        # HERE USE REGEX TO GET THE RIGHT SCH POI, IT MUST SATISFY STARTING WITH '[' OR ',' ,ENDING WITH ',' OR ']', STARTING WITHOUT '"','NUMBER' ,ENDIND WITHOUT '"','NUMBER'
        reg_for_getting_days = "(?<=[\,\[])(?<![\"\d])" + str(pair[0]) + "(?=[\,\]])(?![\d\"])" + '.+' + "(?<![\"\d])(?<=[\,\[])" + str(pair[1]) + "(?![\d\"])(?=[\,\]])"
        #print(reg_for_getting_days)
        schedules_snippet = re.findall(re.compile(reg_for_getting_days), realSchedule + "[END]")
        # if len(schedules_snippet) == 0:
        #     print(realSchedule,reg_for_getting_days)

        days = len(re.findall(r'\d+\":{', schedules_snippet[0]))


        if broadPois[broadSchedulePois[pair[0]]['poi_id']]['type'] == 'Pois::Hotel':
            price_number, currency = calculatePoiPrice(broadSchedulePois[pair[0]]['poi_id'], broadPois, broadCurrencies)
            schHotelPoiDetails.append({"sch_poi_id": pair[0],
                                       "price_number": price_number,
                                       "days": days,
                                       "start_day":current_day,
                                       "type": 'Pois::Hotel',
                                       "is_prepaid": broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"]
                                       # "currency": currency
                                       })
            if broadPois[broadSchedulePois[pair[0]]['poi_id']]["is_prepaid"] == 1:
                totalCost += float(broadPois[broadSchedulePois[pair[0]]['poi_id']]['price_number']) * float(days)
                totalDays += days
        current_day += days
    return totalCost, totalDays, schHotelPoiDetails
def getTourRegionsFromSchedules(schedules, broadSchedulePois, broadPois, broadSchedulePlaces, broadPlaces):
    tourRegions = []
    # here we assume that there are no two same places with different schedule_place_id in one day
    for schedule, schedule_places in schedules.items():
        todayTourRegions = []
        # if debug:
        #     print("schedule", schedule, "-> ", schedule_places)
        for schedule_place, pois in schedule_places.items():
            # print("schedule_place:", schedule_place, "pois: ", pois)
            for poi in pois:
                ## TODO here need a definition of tour places!
                if broadPois[broadSchedulePois[int(poi)]['poi_id']]['type'] in ['Pois::Attraction', 'Pois::Activity',]:
                    region_id = broadPlaces[broadSchedulePlaces[int(schedule_place)]['place_id']]['region_id']
                    #print("poi_id: ", broadSchedulePois[int(poi)]['poi_id'],broadPois[broadSchedulePois[int(poi)]['poi_id']])
                    #print("schedule poi_id: " ,int(poi))
                    #print("region_id: ", region_id)
                    # if debug:
                    #     print("schedule_place",  schedule_place, "place_id",broadSchedulePlaces[int(schedule_place)]['place_id'], "region_id", region_id)
                    if region_id:
                        # if debug:
                        #     print("region", region_id, " schedule_place -> ", schedule_place)
                        todayTourRegions.append(broadPlaces[broadSchedulePlaces[int(schedule_place)]['place_id']]['region_id'])
                    break
        #print("today regions:", todayTourRegions)

        tourRegions += todayTourRegions
        # if debug:
        #     print(tourRegions)
    return tourRegions
def compress(placesOrRegions):
    newPlaceOrRegion = []
    for placeOrRegion in placesOrRegions:
        if not newPlaceOrRegion or newPlaceOrRegion[-1] != placeOrRegion:
            newPlaceOrRegion.append(placeOrRegion)
    return newPlaceOrRegion

def getPlacesFromSchedules(schedules):
    return map(lambda x: int(x[0:-3]), re.findall(r'\d+\"\:\[',schedules))

def getFirstNonTipPoiRaw(part,broadParts,broadPois):
    partPois = broadParts[part]['poi_ids']
    for poi in partPois:
        if broadPois[poi]['type'] != 'Pois::Tip':
            return poi

def getLastNonTipPoiRaw(part,broadParts,broadPois):
    partPois = broadParts[part]['poi_ids']
    for poi in reversed(partPois):
        if broadPois[poi]['type'] != 'Pois::Tip':
            return poi

def station_constraint(prevPart, part, broadPois, broadParts):
    departurePoi = broadPois[getLastNonTipPoiRaw(prevPart, broadParts=broadParts, broadPois=broadPois)]
    currentPoiId = getFirstNonTipPoiRaw(part, broadParts=broadParts, broadPois=broadPois)
    ## 针对美国和加拿大 不加station 限制
    if departurePoi['type'] == 'Pois::Flight' and departurePoi['country_id'] in [11,27]:
        return True
    if departurePoi['type'] == 'Pois::Flight' and departurePoi['arrival_poi_id'] != currentPoiId:
        return False
    elif departurePoi['transport_method'] in ['火车', '轮渡', '缆车', '地铁'] and departurePoi['terminal_station_id'] != currentPoiId:
        return False
    elif broadParts[prevPart]['next_place_id'] != broadParts[part]['head_place_id']:
        return False
    return True


def Id(path):
    """
    MD5加密算法
    :param path:
    :return:
    """
    m = hashlib.md5()
    m.update(str(path).encode('utf-8'))
    return m.hexdigest()
def getTourPlacesFromSchedules(schedules, broadSchedulePois, broadPois, broadSchedulePlaces):
    tourPlaces = []
    # here we assume that there are no two same places with different schedule_place_id in one day
    for schedule, schedule_places in schedules.items():
        todayTourPlaces = []
        for schedule_place, pois in schedule_places.items():
            for poi in pois:
                ## TODO here need a definition of tour places!
                if broadPois[broadSchedulePois[int(poi)]['poi_id']]['type'] in ['Pois::Attraction', 'Pois::Activity']:
                    todayTourPlaces.append(broadSchedulePlaces[int(schedule_place)]['place_id'])
                    break
        tourPlaces += todayTourPlaces
    return tourPlaces

def getFirstAndLastSchAirportPoi(first_schdule, last_schedule, broadSchedulePois, broadPois):
    first_and_last_schdule_pois = itertools.chain.from_iterable(map(lambda x: ast.literal_eval(x), re.findall(r'\[[\d,]+\]', first_schdule + last_schedule)))
    airport_pois = list(filter(lambda x: broadPois[broadSchedulePois[x]['poi_id']]['type'] == 'Pois::Airport', first_and_last_schdule_pois))
    if len(airport_pois) > 0:
        return airport_pois[0], airport_pois[-1]
    else:
        return None, None


def getPathDetail(order, parts, pois, schedulePois, places, schedulePlaces, poiTags, placePoisMapping , regions, countries, currencies, poiCalendar, tagsId):
    base_price = 0.0
    amount = 0.0
    days = 0
    self_drive = False
    rental_car_pois = 0
    hotel_poi_number = 0
    hotel_poi_rating = 0
    lastPart = None
    country_ids = []
    schPoisDetails = []
    tour_regions_list = []
    schedules = mergeSchedules(order, parts)
    schedulePlace_ids = list(itertools.chain.from_iterable(
        map(lambda x: getPlacesFromSchedules(x), [parts[part]['schedules'] for part in order])))

    place_ids = compress(map(lambda x: schedulePlaces[x]['place_id'], schedulePlace_ids))
    place_key = Id(place_ids)
    duplicated_place_ids =getTourPlacesFromSchedules(mergeSchedules(order, parts),
                                                                        broadSchedulePois=schedulePois,
                                                                        broadPois=pois,
                                                                        broadSchedulePlaces=schedulePlaces)
    tour_places_id_order = list(map(lambda x: str(x), compress(duplicated_place_ids)))

    duplicated_tour_region_ids = getTourRegionsFromSchedules(
        mergeSchedules(order, parts),
        broadSchedulePois=schedulePois,
        broadPois=pois,
        broadSchedulePlaces=schedulePlaces,
        broadPlaces=places)
    region_days_counter = Counter(duplicated_tour_region_ids)
    tour_regions_id_order = list(map(lambda x: str(x), compress(duplicated_tour_region_ids)))
    for region, __days in region_days_counter.items():
        tour_regions_list.append({'region_id': region, 'days': __days})
    region_ids = []
    for place in place_ids:
        region_id = places[place]['region_id']
        if region_id and region_id not in region_ids:
            region_ids.append(region_id)
    for part in order:
        country_id = places[parts[part]['place_id']]['country_id']
        if country_id not in country_ids:
            country_ids += [country_id]

        couldMerge = False
        if lastPart != None:
            couldMerge = parts[lastPart]['tail'] == 'incomplete' and parts[part]['head'] == 'incomplete'
        days += len(getKeyFromStrDict(parts[part]['schedules']))
        if couldMerge:
            days -= 1
        lastPart = part
        for poi in parts[part]['poi_ids']:
            if pois[poi]['type'] == 'Pois::CarRental':
                rental_car_pois += 1
            if pois[poi]['type'] == 'Pois::Hotel':
                hotel_poi_number += 1
                hotel_poi_rating += pois[poi]['rating']
            if pois[poi]['type'] == 'Pois::Roadtrip': self_drive = True

        for _, schedulePlacess in extractSchedulesFromPart(part, parts).items():
            for _, schedulePoisArray in schedulePlacess.items():
                for schedulePoi in schedulePoisArray:
                    poi = schedulePois[schedulePoi]['poi_id']
                    if pois[poi]['price_number'] != None and pois[poi]['type'] not in ['Pois::CarRental',
                                                                                       'Pois::Hotel']:
                        amount += float(pois[poi]['price_number'])
                        price_number, currency = calculatePoiPrice(poi, pois, currencies)
                        schPoisDetails.append({"sch_poi_id": schedulePoi,
                                               "price_number": price_number,
                                               "days": 1,
                                               "type": pois[poi]['type'],
                                               "is_prepaid": pois[poi]['is_prepaid']
                                               })
                        if pois[poi]['is_prepaid'] == 1:
                            price_number, _ = calculatePoiPrice(poi, pois, currencies)
                            base_price += price_number
                            ## car renting price
    carRentingCost, schCarRentPoiDetails = getCarRentingCost(
        realSchedule=getRealSchedule(path=order, broadParts=parts), broadPois=pois,
        broadSchedulePois=schedulePois, broadCurrencies=currencies)
    base_price += carRentingCost

    ## hotel price
    hotelCost, hotelDays, schHotelPoiDetails = getHotelCost(
        realSchedule=getRealSchedule(path=order, broadParts=parts),
        broadPois=pois,
        broadSchedulePois=schedulePois,
        broadPlacePoisMapping=placePoisMapping,
        broadCurrencies=currencies)

    if hotelDays > 0:
        average_hotel_price = float(hotelCost) / hotelDays
    else:
        average_hotel_price = 0.0

    base_price += hotelCost
    price = round(base_price * 1.15, 2)
    if hotel_poi_number == 0:
        average_star_rating = 0
    else:
        average_star_rating = round(float(hotel_poi_rating) / hotel_poi_number, 1)
    poi_ids = [poi_id for part in order for poi_id in parts[part]['poi_ids']]
    start_place_id = parts[order[0]]['head_place_id']
    finish_place_id = parts[order[-1]]['tail_place_id']
    ## tags
    tags = map(lambda poi: poiTags[poi], filter(
        lambda x: x in poiTags and pois[x]['type'] in ['Pois::Meal', 'Pois::Activity', 'Pois::Attraction',
                                                       'Pois::Hotel'], poi_ids))
    tags = [item for sublist in tags for item in sublist]
    schPoisDetails += (schCarRentPoiDetails + schHotelPoiDetails)
    poi_key = Id(list(filter(lambda x: pois[x]['type'] != "Pois::Tip", poi_ids)))
    part_key =Id(order)
    region_place_ids = []
    region_place_ids_temp = list(
        map(lambda x: places[x]['region_id'] if places[x]['region_id'] else x, place_ids))
    last = None
    for id in region_place_ids_temp:
        if id != last:
            region_place_ids.append(id)
            last = id
    region_place_key = Id(region_place_ids)
    poi_ids_in_calendar = list(filter(lambda x: x in poiCalendar, poi_ids))
    if len(poi_ids_in_calendar) == 0:
        available_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    else:
        available_months = list(
            reduce(lambda x, y: set(x) & set(y), map(lambda x: poiCalendar[x], poi_ids_in_calendar)))
    destination_id = parts[order[0]]['destination_id']
    first_sch_airport_poi, last_sch_airport_poi = getFirstAndLastSchAirportPoi(
        parts[order[0]]['schedules'], parts[order[-1]]['schedules'], schedulePois, pois)

    return {'part_key': part_key,
            'days': days,
            'poi_ids': poi_ids,
            'attraction_poi_ids': list(filter(lambda x: pois[x]['type'] == "Pois::Attraction", poi_ids)),
            'activity_poi_ids': list(filter(lambda x: pois[x]['type'] == "Pois::Activity", poi_ids)),
            'start_place_id': start_place_id,
            'finish_place_id': finish_place_id,
            'country_ids': country_ids,
            'destination_id': destination_id,
            'price_lower_bound': price,
            'price_upper_bound': price,
            'place_key': place_key,
            'tags': tags,
            'region_place_key': region_place_key,
            'tour_places_id_order': " ".join(tour_places_id_order),
            'first_sch_airport_poi_id': first_sch_airport_poi,
            'last_sch_airport_poi_id': last_sch_airport_poi,
            'place_ids': place_ids,
            'hotel_poi_number': hotel_poi_number,
            'rental_car_pois': rental_car_pois,
            'part_ids': order,
            'region_ids': region_ids,
            'tour_regions': tour_regions_list,
            'tour_regions_id_order': " ".join(tour_regions_id_order),
            'self_drive': self_drive,
            'price': price,
            'poi_key': poi_key,  # 这里要求生成key的poi不包含tip
            'average_hotel_price': average_hotel_price,
            'average_star_rating': average_star_rating,  # -
            'available_months': available_months
            }










