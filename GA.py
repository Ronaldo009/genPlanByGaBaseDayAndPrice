#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 上午11:34
# @Author  : Huang HUi
# @Site    : 
# @File    : GA.py
# @Software: PyCharm


import random
import itertools
from Life import Life
import query_parse
import time
from Gene import Gene
from operator import itemgetter, attrgetter


startParts=query_parse.startParts
nextPartsOf=query_parse.nextPartsOf
prevPartsOf=query_parse.prevPartsOf
endParts=query_parse.endParts
parts=query_parse.parts
pois=query_parse.pois
currencies=query_parse.currencies

class GA(object):
    """遗传算法类"""

    def __init__(self, mutationRate, lifeCount,days,price, matchFun):
      self.mutationRate = mutationRate
      self.lifeCount = lifeCount
      self.days=days
      self.price=price
      self.matchFun = matchFun  # 适配函数
      self.lives = []  # 种群
      self.best = None  # 保存这一代中最好的个体
      self.generation = 1
      self.crossCount = 0
      self.daysDic={}
      self.priceDic={}
      self.mutationCount = 0
      self.bounds = 0.0  # 适配值之和，用于选择是计算概率

      self.initPopulation()



    def initPopulation(self):
        """初始化种群"""
        start1=time.clock()
        self.lives = []
        for i in range(self.lifeCount):
            gene=self.initLife()
            life = Life(gene)
            self.lives.append(life)
        end1=time.clock()
        runtime=end1-start1
        print("----------------初始化种群,用时" + str(("%.2f") % (runtime)) + "秒------------------")

    def judge(self):
        """评估，计算每一个个体的适配值"""
        start=time.clock()
        self.bounds=0.0
        self.bests=[]
        self.notBests=[]
        self.worsts=[]
        self.best =self.lives[0]
        for life in self.lives:
            life.scoreDays,life.scorePrices,days_get,prices_get= self.matchFun(life)
            self.daysDic[tuple(life.gene)]=days_get
            self.priceDic[tuple(life.gene)]=prices_get
            self.bounds+=abs(life.scoreDays)+abs(life.scorePrices)
            if abs(self.best.scoreDays)+abs(self.best.scorePrices)<abs(life.scoreDays)+abs(life.scorePrices):
                self.best=life
        for life in self.lives:
            if abs(life.scoreDays)+abs(life.scorePrices)==2:
                if life not in self.bests:
                    self.bests.append(life)
            if abs(life.scoreDays) + abs(life.scorePrices) == 1.5:
                if life not in self.notBests:
                    self.notBests.append(life)
            if abs(life.scoreDays) + abs(life.scorePrices) < 1.5:
                if life not in self.worsts:
                    self.worsts.append(life)
        end=time.clock()
        runtime=end-start
        print("----------------Judge完成,用时" + str(("%.2f") % (runtime)) + "秒------------------")

    def getGenePrice(self,geneSingle):
        price=0.0
        poi_ids=parts[geneSingle]['poi_ids']
        for poi in poi_ids:
            if float(pois[poi]['price_number']) == 0 or pois[poi]['price_number'] == None:
                price+=0.0
            price += float(pois[poi]['price_number']) * float(currencies[pois[poi]['currency_id']]['rate'])
        return price



    def mutationByDays(self, gene,index1,daysDiff):
        print("mutationByDays")
        newGene=gene[:]
        if  index1==0:
            geneExceptFirst=list(set(prevPartsOf[gene[1]])^set(gene[0:1]))
            if geneExceptFirst:
                for i in geneExceptFirst:
                    day = parts[i]['days']
                    price = self.getGenePrice(i)
                    geneVals = Gene(i, day, price)
                    if abs(geneVals.day-daysDiff)<1:
                        newGene[0]=i
                        break


        elif index1==len(gene)-1:
            geneExceptLast=list(set(nextPartsOf[gene[-2]])^set(gene[-1:]))
            if geneExceptLast:
                for i in geneExceptLast:
                    day = parts[i]['days']
                    price = self.getGenePrice(i)
                    geneVals = Gene(i, day, price)
                    if abs(geneVals.day-daysDiff)<1:
                        newGene[-1]=i
                        break
        else:
            genesMiddle=[]
            midGene=[]
            midGene.append(gene[index1])
            alist=nextPartsOf[gene[index1-1]]
            blist=prevPartsOf[gene[index1+1]]
            ablist=set(alist).intersection(set(blist))
            geneSelect=list(ablist^set(midGene))
            if geneSelect:
                # 只突变一个gene ，成功率比较低
                for i in geneSelect:
                    day = parts[i]['days']
                    price = self.getGenePrice(i)
                    geneVals = Gene(i, day, price)
                    if abs(geneVals.day-daysDiff)<1:
                        genesMiddle.append(i)
                        newGene = gene[:index1] + genesMiddle + gene[index1 + 1:]
                        return newGene
            else:
                # 突变一段基因，成功率增加
                for i in alist:
                    for j in blist:
                        aalist=nextPartsOf[i]
                        bblist=prevPartsOf[j]
                        aabblist=list(set(aalist).intersection(set(bblist)))
                        if aabblist:
                            for k in aabblist:
                                day = parts[k]['days']
                                price = self.getGenePrice(k)
                                geneVals = Gene(k, day, price)
                                if abs(geneVals.day - daysDiff) < 1:
                                    genesMiddle.append(i)
                                    genesMiddle.append(k)
                                    genesMiddle.append(j)
                                    newGene = gene[:index1] + genesMiddle + gene[index1 + 1:]
                                    return newGene

        return newGene

    def mutationByPrices(self, gene,index1,PriceDiff):
        print("mutationByPrices")
        newGene=gene[:]
        if  index1==0:
            geneExceptFirst=list(set(prevPartsOf[gene[1]])^set(gene[0:1]))
            if geneExceptFirst:
                for i in geneExceptFirst:
                    day = parts[i]['days']
                    price = self.getGenePrice(i)
                    geneVals = Gene(i, day, price)
                    if abs(geneVals.price-PriceDiff)<800:
                        newGene[0]=i
                        break


        elif index1==len(gene)-1:
            geneExceptLast=list(set(nextPartsOf[gene[-2]])^set(gene[-1:]))
            if geneExceptLast:
                for i in geneExceptLast:
                    day = parts[i]['days']
                    price = self.getGenePrice(i)
                    geneVals = Gene(i, day, price)
                    if abs(geneVals.price-PriceDiff)<800:
                        newGene[-1]=i
                        break
        else:
            genesMiddle=[]
            midGene=[]
            midGene.append(gene[index1])
            alist=nextPartsOf[gene[index1-1]]
            blist=prevPartsOf[gene[index1+1]]
            ablist=set(alist).intersection(set(blist))
            geneSelect=list(ablist^set(midGene))
            if geneSelect:
                # 只突变一个gene ，成功率比较低
                for i in geneSelect:
                    day = parts[i]['days']
                    price = self.getGenePrice(i)
                    geneVals = Gene(i, day, price)
                    if abs(geneVals.price-PriceDiff)<800:
                        genesMiddle.append(i)
                        newGene = gene[:index1] + genesMiddle + gene[index1 + 1:]
                        return newGene
            else:
                # 突变一段基因，成功率增加
                for i in alist:
                    for j in blist:
                        aalist=nextPartsOf[i]
                        bblist=prevPartsOf[j]
                        aabblist=list(set(aalist).intersection(set(bblist)))
                        if aabblist:
                            for k in aabblist:
                                day = parts[i]['days']
                                price = self.getGenePrice(i)
                                geneVals = Gene(i, day, price)
                                if abs(geneVals.price - PriceDiff) < 800:
                                    genesMiddle.append(i)
                                    genesMiddle.append(k)
                                    genesMiddle.append(j)
                                    newGene = gene[:index1] + genesMiddle + gene[index1 + 1:]
                                    return newGene
        return newGene


    def mutation(self,life):
        # """突变"""
        gene=life.gene
        newGene=gene[:]
        length=len(gene)
         # 产生一个新的基因序列，以免变异的时候影响父种群
        if len(gene)>1:

            try:
                if life.scoreDays>0 and life.scoreDays!=1:
                    geneSortByDay,geneSortByPrice=self.sortByDaysAndPrice(gene)
                    index=geneSortByDay[-1][0]
                    daysDiff=abs(geneSortByDay[-1][2]-(self.daysDic[tuple(life.gene)]-self.days))
                    newGene=self.mutationByDays(gene,index,daysDiff)
                    if newGene==gene:
                        index=geneSortByDay[-2][0]
                        daysDiff=geneSortByDay[-2][2]-(self.daysDic[tuple(life.gene)]-self.days)
                        newGene=self.mutationByDays(gene,index,daysDiff)
                    if newGene==gene:
                        alist=list(set(nextPartsOf[life.gene[0]])^set(life.gene[1]))
                        blist=prevPartsOf[life.gene[-1]]
                        ablist=list(set(alist).intersection(set(blist)))
                        if ablist:
                            newGene=gene[:1]+ablist+gene[-1:]
                        if newGene==gene:
                            alist=nextPartsOf[life.gene[0]]
                            blist=list(set(prevPartsOf[life.gene[-1]])^set(life.gene[-2]))
                            ablist=list(set(alist).intersection(set(blist)))
                            if ablist:
                                newGene=gene[:1]+ablist+gene[-1:]

                    return newGene

                if life.scoreDays<0 and life.scoreDays!=-1:
                    geneSortByDay,geneSortByPrice=self.sortByDaysAndPrice(gene)
                    index=geneSortByDay[0][0]
                    daysDiff=abs(abs(self.daysDic[tuple(life.gene)]-self.days)-geneSortByDay[0][2])
                    newGene=self.mutationByDays(gene,index,daysDiff)
                    if newGene==gene:
                        index=geneSortByDay[1][0]
                        daysDiff = abs(abs(self.daysDic[tuple(life.gene)]-self.days) - geneSortByDay[1][2])
                        newGene=self.mutationByDays(gene,index,daysDiff)
                    if newGene==gene:
                        alist=list(set(nextPartsOf[life.gene[0]])^set(life.gene[1]))
                        blist=prevPartsOf[life.gene[-1]]
                        ablist=list(set(alist).intersection(set(blist)))
                        if ablist:
                            newGene=gene[:1]+ablist+gene[-1:]
                        if newGene==gene:
                            alist=nextPartsOf[life.gene[0]]
                            blist=list(set(prevPartsOf[life.gene[-1]])^set(life.gene[-2]))
                            ablist=list(set(alist).intersection(set(blist)))
                            if ablist:
                                newGene=gene[:1]+ablist+gene[-1:]
                    return newGene

                if life.scorePrices>0 and life.scorePrices!=1:
                    geneSortByDay,geneSortByPrice = self.sortByDaysAndPrice(gene)
                    index = geneSortByPrice[-1][0]
                    priceDiff = abs(geneSortByPrice[-1][3] - (self.priceDic[tuple(life.gene)] - self.price))
                    newGene=self.mutationByPrices(gene, index, priceDiff)
                    if newGene==gene:
                        index=geneSortByPrice[-2][0]
                        priceDiff = abs(geneSortByPrice[-1][3] - (self.priceDic[tuple(life.gene)] - self.price))
                        newGene = self.mutationByPrices(gene, index, priceDiff)
                    if newGene==gene:
                        alist=list(set(nextPartsOf[life.gene[0]])^set(life.gene[1]))
                        blist=prevPartsOf[life.gene[-1]]
                        ablist=list(set(alist).intersection(set(blist)))
                        if ablist:
                            newGene=gene[:1]+ablist+gene[-1:]
                        if newGene==gene:
                            alist=nextPartsOf[life.gene[0]]
                            blist=list(set(prevPartsOf[life.gene[-1]])^set(life.gene[-2]))
                            ablist=list(set(alist).intersection(set(blist)))
                            if ablist:
                                newGene=gene[:1]+ablist+gene[-1:]
                    return newGene
                if life.scorePrices<0 and life.scorePrices!=-1:
                    geneSortByDay,geneSortByPrice = self.sortByDaysAndPrice(gene)
                    index = geneSortByPrice[0][0]
                    priceDiff = abs(abs(self.priceDic[tuple(life.gene)]-self.price  )-geneSortByPrice[0][3])
                    newGene =self.mutationByPrices(gene, index, priceDiff)
                    if newGene==gene:
                        index=geneSortByPrice[1][0]
                        priceDiff = abs(abs(self.priceDic[tuple(life.gene)]-self.price ) - geneSortByPrice[1][3])
                        newGene = self.mutationByPrices(gene, index, priceDiff)
                    if newGene==gene:
                        alist=list(set(nextPartsOf[life.gene[0]])^set(life.gene[1]))
                        blist=prevPartsOf[life.gene[-1]]
                        ablist=list(set(alist).intersection(set(blist)))
                        if ablist:
                            newGene=gene[:1]+ablist+gene[-1:]
                        if newGene==gene:
                            alist=nextPartsOf[life.gene[0]]
                            blist=list(set(prevPartsOf[life.gene[-1]])^set(life.gene[-2]))
                            ablist=list(set(alist).intersection(set(blist)))
                            if ablist:
                                newGene=gene[:1]+ablist+gene[-1:]
                    return newGene
            except:
                return newGene
        return newGene


    def sortByDaysAndPrice(self,gene):
        aa = []

        for i in gene:
            day=parts[i]['days']
            price=self.getGenePrice(i)
            geneVals=Gene(i,day,price)
            aa.append((gene.index(i),geneVals.part, geneVals.day, geneVals.price))
        cc=sorted(aa,key=itemgetter(2))
        bb=sorted(aa,key=itemgetter(3))

        return cc,bb



    def initLife(self):
        newGene = []  # 产生一个新的基因序列，以免变异的时候影响父种群
        flag=True
        while flag:
            try:
                firstpart=random.choice(startParts)
                newGene.append(firstpart)
                if firstpart in endParts:
                    return newGene
                middlePart=random.choice(nextPartsOf[firstpart])
                while 1 :
                    newGene.append(middlePart)
                    if middlePart in endParts:
                        break
                    else:
                        middlePart=random.choice(nextPartsOf[middlePart])
                flag=False
            except:
                flag=True

        return newGene


    # def getOne(self):
    #     """选择一个个体"""
    #     # r = random.uniform(0, self.bounds)
    #     # for life in self.lives:
    #     #     r -= abs(life.scorePrices)+abs(life.scoreDays)
    #     #     if r <= 0:
    #     #         return life
    #
    #
    #     return random.choice(self.notBests)



    def newChild(self):
        """产生新后的"""
        mutationLives=[]

        # 按概率突变
        for i in self.notBests:
            gene = self.mutation(i)
            mutationLives.append(Life(gene))

        return mutationLives

    def next(self):
        start=time.clock()
        """产生下一代"""
        self.judge()
        newLives = []
        newLives.extend(self.newChild())
        while len(newLives) < self.lifeCount:
            newLives.append(Life(self.initLife()))
        self.lives = newLives
        self.generation += 1
        end=time.clock()
        runtime=end-start
        print("----------------迭代一轮需要用时" + str(("%.2f") % (runtime)) + "秒------------------")

