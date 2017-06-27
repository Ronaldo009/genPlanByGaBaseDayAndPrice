#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 上午11:34
# @Author  : Huang HUi
# @Site    : 
# @File    : genPlanByGA.py
# @Software: PyCharm

import argparse
import json
import yaml
import copy
import time
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
import genPlanConstraint
import query_parse

from random import sample

MAXPRICE=999999

countryIds_query=query_parse.countryIds_query
days_query=query_parse.days_query
regions_query=query_parse.regions_query
regionDic_query=query_parse.regionDic_query
pois_query=query_parse.pois_query
regionNotGo_query=query_parse.regionNotGo_query
poiNotGo_query=query_parse.poiNotGo_query
regionSorted_query=query_parse.regionSorted_query
availableMonths_query=query_parse.availableMonths_query
price_query=query_parse.price_query
hotelRating_query=query_parse.hotelRating_query
arrivalRegionId_query=query_parse.arrivalRegionId_query
departRegionId_query=query_parse.departRegionId_query

days_aver=0
if days_query:
    if type(days_query)==int:
        days_aver=days_query
    else:
        days_aver=sum(days_query)/len(days_query)
price_aver=0
if price_query:
    if type(price_query)==int:
        price_aver=price_query
    else:
        price_aver=sum(price_query)/len(price_query)




parts=query_parse.parts
nextPartsOf=query_parse.nextPartsOf
prevPartsOf=query_parse.prevPartsOf
subParts=query_parse.subParts
schedulePois=query_parse.schedulePois
pois=query_parse.pois
planers=query_parse.planers
startParts=query_parse.startParts
endParts=query_parse.endParts
places=query_parse.places
regions=query_parse.regions
countries=query_parse.countries
schedulePlaces=query_parse.schedulePlaces
poiTags=query_parse.poiTags
currencies=query_parse.currencies
poiCalendar=query_parse.poiCalendar
tagsId=query_parse.tagsId
placePoisMapping=query_parse.placePoisMapping




class genPlanByGa(object):

    def __init__(self,lifeCount=100):
        self.lifeCount = lifeCount
        self.ga = GA(mutationRate=0.9,
                     lifeCount=self.lifeCount,
                     days=days_aver,
                     price=price_aver,
                     matchFun=self.matchFun())



    def Asymptotion(self,order):
        result=self.getPriceAndDays(order)
        k1=100
        k2=100
        if days_aver!=0:
            if result['days'] - days_aver>0:
                if (result['days'] - days_aver) > 7 and (result['days'] - days_aver) <= 8:
                    k1=5
                elif (result['days'] - days_aver) > 6 and (result['days'] - days_aver) <= 7:
                    k1 = 4
                elif (result['days'] - days_aver) > 4 and (result['days'] - days_aver) <= 6:
                    k1 = 3
                elif (result['days'] - days_aver) > 2 and (result['days'] - days_aver) <= 4:
                    k1 = 2
                elif result['days'] - days_aver <= 2:
                    k1 = 1
            if days_aver-result['days']>0:
                if days_aver-result['days']>7 and days_aver-result['days']<=8:
                    k1=-5
                if days_aver-result['days']>6 and days_aver-result['days']<=7:
                    k1=-4
                if days_aver-result['days']>4 and days_aver-result['days']<=6:
                    k1=-3
                if days_aver-result['days']>2 and days_aver-result['days']<=4:
                    k1=-2
                if days_aver-result['days']<=2:
                    k1=-1
        else:
            k1=1

        if price_aver!=0:
            if (result['price'] - price_aver) > 0:
                if (result['price']-price_aver)>4000 and (result['price']-price_aver)<=8000:
                    k2=5
                elif (result['price']-price_aver)>2200 and (result['price']-price_aver)<=4000:
                    k2=4
                elif (result['price']-price_aver)>1500 and (result['price']-price_aver)<=2200:
                    k2=3
                elif (result['price']-price_aver)>800 and (result['price']-price_aver)<=1500:
                    k2=2
                elif (result['price']-price_aver)<=800:
                    k2=1
            if (price_aver-result['price']) > 0:
                if (price_aver-result['price']) > 4000 and (price_aver-result['price']) <= 8000:
                    k2 = -5
                elif (price_aver-result['price']) > 2200 and (price_aver-result['price']) <= 4000:
                    k2 = -4
                elif (price_aver-result['price']) > 1500 and (price_aver-result['price']) <= 2200:
                    k2 = -3
                elif (price_aver-result['price']) > 800 and (price_aver-result['price']) <= 1500:
                    k2 = -2
                elif (price_aver-result['price']) <= 800:
                    k2 =- 1

        else:
            k2=1

        return 1/(k1),1/(k2),result['days'],result['price']





    def matchFun(self):
        return  lambda life:self.Asymptotion(life.gene)



    def getPathDetail(self,order):
        base_price = 0.0
        amount = 0.0
        days = 0
        rental_car_pois = 0
        hotel_poi_number = 0
        hotel_poi_rating = 0
        lastPart = None
        country_ids = []
        schPoisDetails = []
        tour_regions_list = []
        schedulePlace_ids = list(itertools.chain.from_iterable(
            map(lambda x: genPlanConstraint.getPlacesFromSchedules(x), [parts[part]['schedules'] for part in order])))

        place_ids = genPlanConstraint.compress(map(lambda x: schedulePlaces[x]['place_id'], schedulePlace_ids))

        duplicated_tour_region_ids = genPlanConstraint.getTourRegionsFromSchedules(
            genPlanConstraint.mergeSchedules(order, parts),
            broadSchedulePois=schedulePois,
            broadPois=pois,
            broadSchedulePlaces=schedulePlaces,
            broadPlaces=places)
        region_days_counter = Counter(duplicated_tour_region_ids)
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
            days += len(genPlanConstraint.getKeyFromStrDict(parts[part]['schedules']))
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

            for _, schedulePlacess in genPlanConstraint.extractSchedulesFromPart(part, parts).items():
                for _, schedulePoisArray in schedulePlacess.items():
                    for schedulePoi in schedulePoisArray:
                        poi = schedulePois[schedulePoi]['poi_id']
                        if pois[poi]['price_number'] != None and pois[poi]['type'] not in ['Pois::CarRental',
                                                                                           'Pois::Hotel']:
                            amount += float(pois[poi]['price_number'])
                            price_number, currency = genPlanConstraint.calculatePoiPrice(poi, pois, currencies)
                            schPoisDetails.append({"sch_poi_id": schedulePoi,
                                                   "price_number": price_number,
                                                   "days": 1,
                                                   "type": pois[poi]['type'],
                                                   "is_prepaid": pois[poi]['is_prepaid']
                                                   })
                            if pois[poi]['is_prepaid'] == 1:
                                price_number, _ = genPlanConstraint.calculatePoiPrice(poi, pois, currencies)
                                base_price += price_number
                                ## car renting price
        carRentingCost, schCarRentPoiDetails = genPlanConstraint.getCarRentingCost(
            realSchedule=genPlanConstraint.getRealSchedule(path=order, broadParts=parts), broadPois=pois,
            broadSchedulePois=schedulePois, broadCurrencies=currencies)
        base_price += carRentingCost

        ## hotel price
        hotelCost, hotelDays, schHotelPoiDetails = genPlanConstraint.getHotelCost(
            realSchedule=genPlanConstraint.getRealSchedule(path=order, broadParts=parts),
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
        schPoisDetails += (schCarRentPoiDetails + schHotelPoiDetails)
        poi_key = genPlanConstraint.Id(list(filter(lambda x: pois[x]['type'] != "Pois::Tip", poi_ids)))
        region_place_ids = []
        region_place_ids_temp = list(
            map(lambda x: places[x]['region_id'] if places[x]['region_id'] else x, place_ids))
        last = None
        for id in region_place_ids_temp:
            if id != last:
                region_place_ids.append(id)
                last = id
        poi_ids_in_calendar = list(filter(lambda x: x in poiCalendar, poi_ids))
        if len(poi_ids_in_calendar) == 0:
            available_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        else:
            available_months = list(
                reduce(lambda x, y: set(x) & set(y), map(lambda x: poiCalendar[x], poi_ids_in_calendar)))

        return {
                'days': days,
                'poi_ids': poi_ids,
                'country_ids': country_ids,
                'hotel_poi_number': hotel_poi_number,
                'rental_car_pois': rental_car_pois,
                'part_ids': order,
                'region_ids': region_ids,
                'tour_regions': tour_regions_list,
                'price': price,
                'poi_key': poi_key,  # 这里要求生成key的poi不包含tip
                'average_hotel_price': average_hotel_price,
                'average_star_rating': average_star_rating,  # -
                'available_months': available_months
                }





    def querySatisfied(self,result):
        if days_query:
            if type(days_query)==list:
                if result['days'] <days_query[0] or result["days"]>days_query[-1]:
                    print(result['days'])
                    return False
            if type(days_query)==int:
                if result['days']!=days_query:
                    return False
        if price_query:
            if result['price'] > price_query[1] or result['price'] <price_query[0]:
                print("price")
                return False
        if pois_query:
            if set(pois_query)-set(result['poi_ids']):
                print("pois")
                return False
        if regions_query:
            regionsMapInGenPlan ={x['region_id']:x['days'] for x in result['tour_regions']}

            regionsMapInQuery = {x['region_id']:x['day'] for x in regions_query}
            if set(regionsMapInQuery.keys()) - set(regionsMapInGenPlan.keys()):
                print("regionDays")
                return False
            for regionId, days in regionsMapInQuery.items():
                if days and regionsMapInGenPlan[regionId] != days:
                    print("regionDays")
                    return False
        if regionNotGo_query:
            if set(result['region_ids']) & set(regionNotGo_query):
                print("region_ids")
                return False
        if poiNotGo_query:
            if set(result['poi_ids']) & set(poiNotGo_query):
                return False
        if availableMonths_query:
            if set(availableMonths_query)-set(result['available_months']):
                return False
        if departRegionId_query:
            if departRegionId_query and places[parts[result['part_ids'][-1]]['place_id']]['region_id']!=departRegionId_query:
                return False
        if arrivalRegionId_query:
            if arrivalRegionId_query and places[parts[result['part_ids'][0]]['place_id']]['region_id']!=arrivalRegionId_query:
                return False
        if hotelRating_query:
            if hotelRating_query and hotelRating_query!=result['average_star_rating']:
                return False

        if result['hotel_poi_number']==0:
            print("hotel")
            return False
        if result['rental_car_pois']%2!=0:
            print("carRental")
            return False
        depuPoi=[]
        if len(set(result['poi_ids']))!=len(result['poi_ids']):
            for i in result['poi_ids']:
                if result['poi_ids'].count(i) > 1:
                    depuPoi.append(i)
            for i in set(depuPoi):
                if pois[i]['type'] not in ['Pois::CarRental', 'Pois::Airport', 'Pois::Hub']:
                    return False

        for i in range(len(result['part_ids'])-1):
            if not genPlanConstraint.station_constraint(result['part_ids'][i],result['part_ids'][i+1],pois,parts):
                return False
        return True


    def getPriceAndDays(self,order):
        base_price = 0.0
        amount = 0.0
        days = 0
        lastPart = None
        for part in order:
            couldMerge = False
            if lastPart != None:
                couldMerge = parts[lastPart]['tail'] == 'incomplete' and parts[part]['head'] == 'incomplete'
            days += len(genPlanConstraint.getKeyFromStrDict(parts[part]['schedules']))
            if couldMerge:
                days -= 1
            for _, schedulePlacess in genPlanConstraint.extractSchedulesFromPart(part, parts).items():
                for _, schedulePoisArray in schedulePlacess.items():
                    for schedulePoi in schedulePoisArray:
                        poi = schedulePois[schedulePoi]['poi_id']
                        if pois[poi]['price_number'] != None and pois[poi]['type'] not in ['Pois::CarRental',
                                                                                           'Pois::Hotel']:
                            amount += float(pois[poi]['price_number'])
                            price_number, currency = genPlanConstraint.calculatePoiPrice(poi, pois, currencies)
                            if pois[poi]['is_prepaid'] == 1:
                                base_price += price_number
                                ## car renting price
        carRentingCost, schCarRentPoiDetails = genPlanConstraint.getCarRentingCost(
            realSchedule=genPlanConstraint.getRealSchedule(path=order, broadParts=parts), broadPois=pois,
            broadSchedulePois=schedulePois, broadCurrencies=currencies)
        base_price += carRentingCost

        ## hotel price
        hotelCost, hotelDays, schHotelPoiDetails = genPlanConstraint.getHotelCost(
            realSchedule=genPlanConstraint.getRealSchedule(path=order, broadParts=parts),
            broadPois=pois,
            broadSchedulePois=schedulePois,
            broadPlacePoisMapping=placePoisMapping,
            broadCurrencies=currencies)
        base_price += hotelCost
        price = round(base_price * 1.15, 2)
        return {
                'days': days,
                'price': price,

                }



    def run(self,n=0):
        start=time.clock()
        result=[]
        resultMD5=[]
        while n>0:
            self.ga.next()
            # score=self.Asymptotion(self.ga.best.gene)
            # print(("%d,%d")%(self.ga.generation,score))
            for i in self.ga.bests:
                if i not in result:
                    result.append(i.gene)
            result.sort()
            result=list(result for result,_ in itertools.groupby(result))
            n=n-1
        for i in result:
            pathDetail = self.getPathDetail(i)
            if self.querySatisfied(pathDetail):
                resultMD5.append(i)
        end=time.clock()
        runtime=end-start
        return resultMD5,runtime


if __name__ == '__main__':
    iterNums=50
    gpGa=genPlanByGa()
    result,runtime=gpGa.run(iterNums)
    for i,items in enumerate(result):
            print(i,items)
    print("共用时"+str(("%.2f")%(runtime))+"秒")


















