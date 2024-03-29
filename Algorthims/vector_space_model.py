import json
import sys
import string
import re
import os
from os.path import dirname, abspath, join
import pandas as pd
from pandas.io.json import json_normalize
import numpy as np
import glob
# to support relative import
sys.path.append(dirname(dirname(abspath(__file__))))
from back import clean

display = pd.options.display

# display.max_columns = 1000
# display.max_rows = 1000
# display.max_colwidth = 199
# display.width = None

class VectorSpace():
    def __init__(self):
        self.invertedIndex = {}
        self.positionalIndex = {}
        self.path = dirname(dirname(abspath(__file__)))
        os.chdir(self.path)
        self.df = {}
        self.tf = {}
        self.tfidf = {}
        self._loadData()
        self.calculateDF()
        self.tf = pd.DataFrame.from_dict(self.positionalIndex,orient='index')


    def _loadData(self):
        with open(self.path+"/back/inverted_index.json", "r") as json_file:
            self.invertedIndex = json.load(json_file)
        with open(self.path+"/back/postional_index.json", "r") as json_file:
            self.positionalIndex = json.load(json_file)
    
    def getData(self):
        with open(self.path+"/Algorthims/tfidf.json", "r") as json_file:
            self.tfidf = pd.read_json(json.load(json_file))
        # print(self.tfidf)
    
    def getQueryPosting(self, query):
        query_posting = clean.preprocessQuery(query)
        return query_posting
    
    def calculateQueryTF(self,query):
        invertedIndex = clean.queryInvertedIndex(query)
        temp = invertedIndex.copy()
        for term in temp:
            if term not in self.invertedIndex:
                # adding terms to the tfidf matrix if they are new to the collection.
                # adding DF = 0  if they are new to the collection.
                    # self.tfidf.loc[term] = [0 for i in range(0,len(self.tfidf.columns))]
                    # self.df[term] = 0
                invertedIndex.pop(term,None)
        qTF = {}
        # converting invertedIndex to the TF for the query.
        for item,v in invertedIndex.items():
            qTF[item] = len(v)
        return qTF

    def calculateQueryTF_IDF(self,query):
        qTF = self.calculateQueryTF(query)
        if qTF == {}:
            return 500
        x,y = self.tfidf.shape
        self.tfidf['q'] = self.tfidf.index.map(qTF)
        self.tfidf['q'] = self.tfidf['q'].fillna(0)
        # print(self.tfidf)

        df = self.df
        tf = self.tfidf['q'].copy()

        for i in self.tfidf.index:
            self.tfidf['q'][i]= (np.log10(tf[i]+1) )* np.log10(y/df[i])
        # print(self.tfidf)
    
    def calculateDF(self):
        for dic,posting in self.invertedIndex.items():
            self.df[dic] = len(posting)
        # print(self.df)
    
    def calculateTF(self):
        # List of Docs names
        cols = list(self.tf.columns)
        # No. of terms and No. of docs
        x,y = self.tf.shape
        # fill NaNs with zeros
        self.tf = self.tf.fillna(0)
        for i in range(0,x):
            for j in range(0,y):
                if self.tf.iat[i,j] !=0:
                    self.tf.iat[i,j] = len(self.tf.iat[i,j]) 
        # print(self.tf)

    def calculateTF_IDF(self):
        self.tfidf = self.tf.copy()
        x,y = self.tfidf.shape
        terms = list(self.tfidf.index)
        self.tfidf.index.name = 'term'
        for t in range(0,x):
            term = terms[t]
            df = self.df[term]
            for d in range(0,y):
                tf = self.tf.iat[t,d]
                self.tfidf.iat[t,d] = ( np.log10(tf+1) )* np.log10(y/df)
        with open("Algorthims/tfidf.json","w") as outputfile:
            # json.dump(self.tfidf.to_json(orient='records'),outputfile)
            json.dump(self.tfidf.to_json(),outputfile)
        # print(self.tfidf)

    def cosineSimlarity(self,doc1,doc2):
        numerator = 0
        eucLen1 = 0
        eucLen2 = 0
        for i in range(0,len(doc1)):
            numerator += doc1[i]*doc2[i]
            eucLen1 += np.power(doc1[i],2)
            eucLen2 += np.power(doc2[i],2)
        return numerator / np.sqrt(eucLen1) * np.sqrt(eucLen2)

    def similarity(self,flag=False):
        self.simMatrix = {}
        
        q = self.tfidf['q']
        for doc in self.tfidf.columns:
            if doc != 'q':
                self.simMatrix[doc] = self.cosineSimlarity(self.tfidf[doc].copy(),q)
        if flag:
            return self.simMatrix

        self.simMatrix = sorted([(x,y) for x,y in self.simMatrix.items()],key=lambda x: x[1], reverse = True)
        return [i[0] for i in self.simMatrix]
        # print(self.simMatrix)
    
    def freeTextQueryWrapper(self,query):
        self.getData()
        result = self.calculateQueryTF_IDF(self.getQueryPosting(query))
        if result == 500:
            return {"error": "500"} 
        result = self.similarity()
        score = self.similarity(True)
        data = clean.getData()
        final = {}
        
        for res in result:
            final[res] = data[int(res)-1]
            final[res]['score'] = score[res]
        return final
        


if __name__ == "__main__":
    x= VectorSpace()
    x.calculateDF()
    x.calculateTF()
    x.calculateTF_IDF()
    # print(x.freeTextQueryWrapper("apple"))