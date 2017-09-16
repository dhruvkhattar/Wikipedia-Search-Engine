from collections import defaultdict
from indexer import Doc
import pdb
import sys
import threading
import math
import re
import timeit

offset = []
titleOffset = []

def findFileNo(low, high, offset, word, f, typ='str'):

    while low < high:
        mid = int((low + high) / 2)
        f.seek(offset[mid])
        wordPtr = f.readline().strip().split()
        #try:
        #    print(low, high, mid, offset[mid], wordPtr[0], word)
        #except:
        #    pdb.set_trace()
        if typ == 'int':
            if int(word) == int(wordPtr[0]):
                return wordPtr[1:], mid
            elif int(word) > int(wordPtr[0]):
                low = mid + 1
            else:
                high = mid
        else:
            if word == wordPtr[0]:
                #print(wordPtr[0], mid)
                return wordPtr[1:], mid
            elif word > wordPtr[0]:
                low = mid + 1
            else:
                high = mid
    return [], -1


def findDocs(filename, fileNo, field, word, fieldFile):

    fieldOffset = []
    docFreq = []
    with open('../data/offset_' + field + fileNo + '.txt') as f:
        for line in f:
            offset, df = line.strip().split()
            fieldOffset.append(int(offset))
            docFreq.append(int(df))
    docList, mid = findFileNo(0, len(fieldOffset), fieldOffset, word, fieldFile)
    return docList, docFreq[mid]


def fieldQuery(words, fields, fvocab):

    docList = defaultdict(dict)
    docFreq = {}
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
            returnedList, df = findDocs(filename, fileNo, field, word, fieldFile)
            docList[word][field] = returnedList
            docFreq[word] = df
    return docList, docFreq


def simpleQuery(words, fvocab):

    docList = defaultdict(dict)
    docFreq = {}
    fields = ['t', 'b', 'i', 'c', 'r', 'l']
    for word in words:
        docs, mid = findFileNo(0, len(offset), offset, word, fvocab)
        if len(docs) > 0:
            fileNo = docs[0]
            docFreq[word] = docs[1]
            for field in fields:
                #print(word, field)
                filename = '../data/' + field + str(fileNo) + '.txt'
                fieldFile = open(filename, 'r')
                returnedList, _ = findDocs(filename, fileNo, field, word, fieldFile)
                docList[word][field] = returnedList
    return docList, docFreq


def rank(results, docFreq, nfiles, qtype):

    docs = defaultdict(float)

    #s1 = defaultdict(int)
    #s2 = defaultdict(int)
    queryIdf = {}

    for key in docFreq:
        queryIdf[key] = math.log((float(nfiles) - float(docFreq[key]) + 0.5) / ( float(docFreq[key]) + 0.5))
        docFreq[key] = math.log(float(nfiles) / float(docFreq[key]))

    for word in results:
        fieldWisePostingList = results[word]
        for field in fieldWisePostingList:
            if len(field) > 0:
                field = field
                postingList = fieldWisePostingList[field]
                if field == 't':
                    factor = 0.25
                if field == 'b':
                    factor = 0.25
                if field == 'i':
                    factor = 0.20
                if field == 'c':
                    factor = 0.1
                if field == 'r':
                    factor = 0.05
                if field == 'l':
                    factor = 0.05
                for i in range(0, len(postingList), 2):
                    #s1[postingList[i]] += float((1 + math.log(float(postingList[i+1]))) * docFreq[word]) ** 2
                    #s2[postingList[i]] += float(queryIdf[word]) ** 2
                    docs[postingList[i]] += float( factor * (1+math.log(float(postingList[i+1]))) * docFreq[word])
    
    #for key in docs:
    #    docs[key] /= float(math.sqrt(s1[key])) * float(math.sqrt(s2[key]))

    return docs


def search():

    print('Loading Search Engine\n')
    with open('../data/titleOffset.txt', 'r') as f:
        for line in f:
            titleOffset.append(int(line.strip()))

    with open('../data/offset.txt', 'r') as f:
        for line in f:
            offset.append(int(line.strip()))
    
    fvocab = open('../data/vocab.txt', 'r')
    titleFile = open('../data/title.txt', 'r')
    f = open('../data/fileNumbers.txt', 'r')
    nfiles = int(f.read().strip())
    f.close()

    d = Doc()

    while True:
        query = input('\nType in your query:\n')
        start = timeit.default_timer()
        query = query.lower()
    
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
            results = rank(results, docFreq, nfiles, 'f')
        else:
            tokens = d.tokenize(query)
            tokens = d.removeStopWords(tokens)
            tokens = d.stem(tokens)
            results, docFreq = simpleQuery(tokens, fvocab)
            results = rank(results, docFreq, nfiles, 's')


        print('\nResults:\n')
        if len(results) > 0:
            results = sorted(results, key=results.get, reverse=True)
            results = results[:10]
            for key in results:
                title, _ = findFileNo(0, len(titleOffset), titleOffset, key, titleFile, 'int')
                print(' '.join(title))
        end = timeit.default_timer()
        print('Time taken =', end-start)


if __name__ == '__main__':

    search()
