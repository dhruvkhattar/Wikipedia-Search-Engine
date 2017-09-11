from collections import defaultdict
from indexer import Doc
import pdb
import sys
import threading
import math
import re

offset = []
titleOffset = []

def findFileNo(low, high, offset, word, f, typ='str'):

    while low < high:
        mid = int((low + high) / 2)
        f.seek(offset[mid])
        testWord = f.readline().strip().split()
        try:
            print(low, high, mid, offset[mid], testWord[0], word)
        except:
            pdb.set_trace()
        if typ == 'int':
            if int(word) == int(testWord[0]):
                return testWord[1:], mid
            elif int(word) > int(testWord[0]):
                low = mid + 1
            else:
                high = mid
        else:
            if word == testWord[0]:
                print(testWord[0], mid)
                return testWord[1:], mid
            elif word > testWord[0]:
                low = mid + 1
            else:
                high = mid
    return [], -1


def findFileList(filename, fileNo, field, word, fieldFile):

    fieldOffset = []
    tempdf = []
    with open('../data/offset_' + field + fileNo + '.txt') as f:
        for line in f:
            offset, docFreq = line.strip().split()
            fieldOffset.append(int(offset))
            tempdf.append(int(docFreq))
    fileList, mid = findFileNo(0, len(fieldOffset), fieldOffset, word, fieldFile)
    return fileList, tempdf[mid]


def fieldQuery(words, fields, fvocab):

    fileList = defaultdict(dict)
    df = {}
    for i in range(len(words)):
        word = words[i]
        field = fields[i]
        docs, mid = findFileNo(0, len(offset), offset, word, fvocab)
        print('docs')
        print(docs)
        if len(docs) > 0:
            fileNo = docs[0]
            filename = '../data/' + field + str(fileNo) + '.txt'
            fieldFile = open(filename, 'r')
            returnedList, docFreq = findFileList(filename, fileNo, field, word, fieldFile)
            fileList[word][field] = returnedList
            df[word] = docFreq
    return fileList, df

def simpleQuery(words, fvocab):

    fileList = defaultdict(dict)
    df = {}
    fields = ['t', 'b', 'i', 'c', 'r', 'l']
    for word in words:
        docs, mid = findFileNo(0, len(offset), offset, word, fvocab)
        if len(docs) > 0:
            fileNo = docs[0]
            df[word] = docs[1]
            for field in fields:
                print(word, field)
                filename = '../data/' + field + str(fileNo) + '.txt'
                fieldFile = open(filename, 'r')
                returnedList, _ = findFileList(filename, fileNo, field, word, fieldFile)
                fileList[word][field] = returnedList
    return fileList, df

def rank(results, docFreq, noOfFiles):

    docs = defaultdict(float)

    for key in docFreq:
        docFreq[key] = math.log((float(docFreq[key]) / float(noOfFiles-1)))

    for word in results:
        fieldWisePostingList = results[word]
        for key in fieldWisePostingList:
            if len(key) > 0:
                field = key
                postingList = fieldWisePostingList[key]
                if key == 't':
                    factor = 0.3
                if key == 'b':
                    factor = 0.25
                if key == 'i':
                    factor = 0.15
                if key == 'c':
                    factor = 0.15
                if key == 'r':
                    factor = 0.5
                if key == 'l':
                    factor = 0.5
                for i in range(0, len(postingList), 2):
                    docs[postingList[i]] += float(postingList[i+1])

    return docs


def search():
    
    with open('../data/titleOffset.txt', 'r') as f:
        for line in f:
            titleOffset.append(int(line.strip()))

    with open('../data/offset.txt', 'r') as f:
        for line in f:
            offset.append(int(line.strip()))
    
    fvocab = open('../data/vocab.txt', 'r')

    d = Doc()

    while True:
        query = input()
        query.lower()
        flag = 0
    
        if re.match(r'[t|b|i|c|r|l]:', query):
            flag = 1
            words = query.strip().split(' ')
            fields = []
            tokens = []
            for key in words:
                fields.append(key[0])
                tokens.append(key[2:])
            tokens = d.removeStopWords(tokens)
            tokens = d.stem(tokens)
            results, docFreq = fieldQuery(tokens, fields, fvocab)
        else:
            tokens = d.tokenize(query)
            tokens = d.removeStopWords(tokens)
            tokens = d.stem(tokens)
            results, docFreq = simpleQuery(tokens,  fvocab)

        
        f = open('../data/fileNumbers.txt', 'r')
        noOfFiles = int(f.read().strip())
        f.close()

        print('results')
        print(results)
        results = rank(results, docFreq, noOfFiles)
        titleFile = open('../data/title.txt', 'r')
        dictTitle = {}

        for key in sorted(results.keys()):
            title, _ = findFileNo(0, len(titleOffset), titleOffset, key, titleFile, 'int')
            dictTitle[key] = ' '.join(title)
    
        if len(results) > 0:
            results = sorted(results, key=results.get, reverse=True)
            results = results[:10]
            print(results[0])
            for key in results:
                print(dictTitle[key])

        print('done')

if __name__ == '__main__':

    search()
