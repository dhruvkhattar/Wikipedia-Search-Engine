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
        #try:
        #    print(low, high, mid, offset[mid], testWord[0], word)
        #except:
        #    pdb.set_trace()
        if typ == 'int':
            if int(word) == int(testWord[0]):
                return testWord[1:], mid
            elif int(word) > int(testWord[0]):
                low = mid + 1
            else:
                high = mid
        else:
            if word == testWord[0]:
                #print(testWord[0], mid)
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
        #print('docs')
        #print(docs)
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
                #print(word, field)
                filename = '../data/' + field + str(fileNo) + '.txt'
                fieldFile = open(filename, 'r')
                returnedList, _ = findFileList(filename, fileNo, field, word, fieldFile)
                fileList[word][field] = returnedList
    return fileList, df


def rank(results, docFreq, noOfFiles):

    docs = defaultdict(float)

    denom = 1 / float(math.sqrt(len(docFreq)))
    s = defaultdict(int)
    for key in docFreq:
        docFreq[key] = math.log((float(noOfFiles) / float(docFreq[key])))

    for word in results:
        fieldWisePostingList = results[word]
        for field in fieldWisePostingList:
            if len(field) > 0:
                field = field
                postingList = fieldWisePostingList[field]
                if field == 't':
                    factor = 0.3
                if field == 'b':
                    factor = 0.25
                if field == 'i':
                    factor = 0.15
                if field == 'c':
                    factor = 0.15
                if field == 'r':
                    factor = 0.05
                if field == 'l':
                    factor = 0.05
                for i in range(0, len(postingList), 2):
                    s[postingList[i]] += float(postingList[i+1]) ** 2
                    docs[postingList[i]] += float(denom * factor * math.log(1 + float(postingList[i+1])) * docFreq[word])
    
    for key in docs:
        docs[key] /= float(math.sqrt(s[key]))

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
        query = input('Type in your query:\n')
        query.lower()
    
        if re.match(r'[t|b|i|c|r|l]:', query):
            words = re.findall(r'[t|b|c|i|l|r]:([^:]*)(?!\S)', query)
            tempFields = re.findall(r'([t|b|c|i|l|r]):', query)
            tokens = []
            fields = []
            for i in range(len(words)):
                for word in words[i].split():
                    fields.append(tempFields[i])
                    tokens.append(word)
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

        results = rank(results, docFreq, noOfFiles)
        titleFile = open('../data/title.txt', 'r')
        dictTitle = {}

        if len(results) > 0:
            print(results)
            results = sorted(results, key=results.get, reverse=True)
            results = results[:10]
            #print(results[0])
            for key in results:
                title, _ = findFileNo(0, len(titleOffset), titleOffset, key, titleFile, 'int')
                print(' '.join(title))


if __name__ == '__main__':

    search()
