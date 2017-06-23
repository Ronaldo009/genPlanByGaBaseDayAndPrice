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
      self.days=days,
      self.price=price,
      self.matchFun = matchFun  # 适配函数
      self.lives = []  # 种群
      self.best = None  # 保存这一代中最好的个体
      self.generation = 1
      self.crossCount = 0
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
        self.best =self.lives[0]
        for life in self.lives:
            life.scoreDays,life.scorePrices = self.matchFun(life)
            for gene in life.gene:
                gene.days=parts[gene]['days']
                gene.price=self.getGenePrice(gene)
            self.bounds+=(life.scoreDays+life.scorePrices)
            if self.best.scoreDays+self.best.scorePrices<life.scoreDays+life.scorePrices:
                self.best=life
        end=time.clock()
        runtime=end-start
        print("----------------Judge完成,用时" + str(("%.2f") % (runtime)) + "秒------------------")

    def getGenePrice(self,gene):
        price=0.0
        poi_ids=parts[gene]['poi_ids']
        for poi in poi_ids:
            if float(pois[poi]['price_number']) == 0 or pois[poi]['price_number'] == None:
                return 0.0, "None"
            price = float(pois[poi]['price_number']) * float(currencies[pois[poi]['currency_id']]['rate'])
        return price

    # def cross(self, parent1, parent2):
    #     """交叉"""
    #     index1 = random.randint(0, self.geneLenght - 1)
    #     index2 = random.randint(index1, self.geneLenght - 1)
    #     tempGene = parent2.gene[index1:index2]  # 交叉的基因片段
    #     newGene = []
    #     p1len = 0
    #     for g in parent1.gene:
    #         if p1len == index1:
    #             newGene.extend(tempGene)  # 插入基因片段
    #             p1len += 1
    #         if g not in tempGene:
    #             newGene.append(g)
    #             p1len += 1
    #     self.crossCount += 1
    #     return newGene

    def mutation(self, gene):
        """突变"""
        newGene = gene[:]
         # 产生一个新的基因序列，以免变异的时候影响父种群
        if len(gene)>1:
            flag=True
            while flag:
                try:
                    flag = False
                    index1 = random.randint(0, len(gene) - 1)
                    if  index1==0:
                        geneExceptFirst=list(set(prevPartsOf[gene[1]])^set(gene[0:1]))
                        if geneExceptFirst :
                            geneStart=random.choice(geneExceptFirst)
                            newGene[0]=geneStart

                    elif index1==len(gene)-1:
                        geneExceptLast=list(set(nextPartsOf[gene[-2]])^set(gene[-1:]))
                        if geneExceptLast:
                            geneLast=random.choice(geneExceptLast)
                            newGene[-1]=geneLast
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
                            genesMiddle.append(random.choice(geneSelect))
                            newGene=gene[:index1]+genesMiddle+gene[index1+1:]
                            return newGene
                        else:
                            # 突变一段基因，成功率增加
                            for i in alist:
                                for j in blist:
                                    aalist=nextPartsOf[i]
                                    bblist=prevPartsOf[j]
                                    aabblist=list(set(aalist).intersection(set(bblist)))
                                    if aabblist:
                                        genesMiddle.append(i)
                                        genesMiddle.append(random.choice(aabblist))
                                        genesMiddle.append(j)
                                        newGene=gene[:index1]+genesMiddle+gene[index1+1:]
                                        return newGene
                except:
                    flag=True

        return newGene


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


    def getOne(self):
        """选择一个个体"""
        r = random.uniform(0, self.bounds)
        for life in self.lives:
            r -= (life.scorePrices+life.scoreDays)
            if r <= 0:
                return life



    def newChild(self):
        """产生新后的"""
        parent1 = self.getOne()
        gene=parent1.gene


        # 按概率突变
        rate = random.random()
        if rate < self.mutationRate:
            gene = self.mutation(gene)

        return Life(gene)

    def next(self):
        start=time.clock()
        """产生下一代"""
        self.judge()
        newLives = []
        newLives.append(self.best)  # 把最好的个体加入下一代
        while len(newLives) < self.lifeCount:
            newLives.append(self.newChild())
        self.lives = newLives
        self.generation += 1
        end=time.clock()
        runtime=end-start
        print("----------------迭代一轮需要用时" + str(("%.2f") % (runtime)) + "秒------------------")

