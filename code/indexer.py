import sys
import heapq
import operator
from collections import defaultdict
import timeit
import re
import os
import pdb
import xml.sax
from nltk.corpus import stopwords
from nltk.stem.porter import *
import Stemmer
import threading
from unidecode import unidecode
from tqdm import tqdm

stemmer = Stemmer.Stemmer('english')
#stemmer = PorterStemmer()

stopWords = set(stopwords.words('english'))
stop_dict = defaultdict(int)
for word in stopWords:
    stop_dict[word] = 1

indexMap = defaultdict(list)
fileCount = 0
pageCount = 0
dictID = {}
offset = 0

class Doc():

    def __init__(self):

        pass


    def tokenize(self, data):
    
        data = data.encode("ascii", errors="ignore").decode()
        data = re.sub(r'http[^\ ]*\ ', r' ', data) # removing urls
        data = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', data) # removing html entities
        data = re.sub(r'\—|\%|\$|\'|\||\.|\*|\[|\]|\:|\;|\,|\{|\}|\(|\)|\=|\+|\-|\_|\#|\!|\`|\"|\?|\/|\>|\<|\&|\\|\u2013|\n', r' ', data) # removing special characters
        return data.split()

    
    def removeStopWords(self, data):
        
        return [w for w in data if stop_dict[w] != 1]


    def stem(self, data):
        
        return stemmer.stemWords(data)
        #return [stemmer.stem(x) for x in data]


    def processText(self, ID, text, title):
        
        text = text.lower() #Case Folding
        data = text.split('==references==')
        if len(data) == 1:
            data = text.split('== references == ')
        if len(data) == 1:
            references = []
            links = []
            categories = []
        else:
            references = self.extractReferences(data[1])
            links = self.extractExternalLinks(data[1])
            categories = self.extractCategories(data[1])
        info = self.extractInfobox(data[0])
        body = self.extractBody(data[0])
        title = self.extractTitle(title.lower())
    
        return title, body, info, categories, links, references


    def extractTitle(self, text):

        data = self.tokenize(text)
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


    def extractBody(self, text):

        data = re.sub(r'\{\{.*\}\}', r' ', text)
        
        data = self.tokenize(data)
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


    def extractInfobox(self, text):

        data = text.split('\n')
        flag = 0
        info = []
        for line in data:
            if re.match(r'\{\{infobox', line):
                flag = 1
                info.append(re.sub(r'\{\{infobox(.*)', r'\1', line))
            elif flag == 1:
                if line == '}}':
                    flag = 0
                    continue
                info.append(line)

        data = self.tokenize(' '.join(info))
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


    def extractReferences(self, text):

        data = text.split('\n')
        refs = []
        for line in data:
            if re.search(r'<ref', line):
                refs.append(re.sub(r'.*title[\ ]*=[\ ]*([^\|]*).*', r'\1', line))

        data = self.tokenize(' '.join(refs))
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


    def extractCategories(self, text):
        
        data = text.split('\n')
        categories = []
        for line in data:
            if re.match(r'\[\[category', line):
                categories.append(re.sub(r'\[\[category:(.*)\]\]', r'\1', line))
        
        data = self.tokenize(' '.join(categories))
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


    def extractExternalLinks(self, text):
        
        data = text.split('\n')
        links = []
        for line in data:
            if re.match(r'\*[\ ]*\[', line):
                links.append(line)
        
        data = self.tokenize(' '.join(links))
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data
 
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


class Indexer():

    def __init__(self, title, body, info, categories, links, references):

        self.title = title
        self.body = body
        self.info = info
        self.categories = categories
        self.links = links
        self.references = references


    def createIndex(self):

        global pageCount
        global fileCount
        global indexMap
        global offset
        global dictID

        ID = pageCount
        words = defaultdict(int)
        d = defaultdict(int)
        for word in self.title:
            d[word] += 1
            words[word] += 1
        title = d
        
        d = defaultdict(int)
        for word in self.body:
            d[word] += 1
            words[word] += 1
        body = d

        d = defaultdict(int)
        for word in self.info:
            d[word] += 1
            words[word] += 1
        info = d
	
        d = defaultdict(int)
        for word in self.categories:
            d[word] += 1
            words[word] += 1
        categories = d
        
        d = defaultdict(int)
        for word in self.links:
            d[word] += 1
            words[word] += 1
        links = d
        
        d = defaultdict(int)
        for word in self.references:
            d[word] += 1
            words[word] += 1
        references = d
    
        for word in words.keys():
            t = title[word]
            b = body[word]
            i = info[word]
            c = categories[word]
            l = links[word]
            r = references[word]
            string = 'd'+str(ID)
            if t:
                string += 't' + str(t)
            if b:
                string += 'b' + str(b)
            if i:
                string += 'i' + str(i)
            if c:
                string += 'c' + str(c)
            if l:
                string += 'l' + str(l)
            if r:
                string += 'r' + str(r)

            indexMap[word].append(string)
        
        pageCount += 1
        if pageCount%20000 == 0:
            offset = writeIntoFile(indexMap, dictID, fileCount, offset)
            indexMap = defaultdict(list)
            dictID = {}
            fileCount += 1


class writeThread(threading.Thread):

    def __init__(self, field, data, offset, count):

        threading.Thread.__init__(self)
        self.field = field
        self.data = data
        self.count = count
        self.offset = offset

    def run(self):

        filename = '../data/' + self.field + str(self.count) + '.txt'
        with open(filename, 'w') as f:
            f.write('\n'.join(self.data))
        
        filename = '../data/offset_' + self.field + str(self.count) + '.txt'
        with open(filename, 'w') as f:
            f.write('\n'.join(self.offset))


def writeFinalIndex(data, finalCount, offsetSize):

    title = defaultdict(dict)
    body = defaultdict(dict)
    info = defaultdict(dict)
    category = defaultdict(dict)
    link = defaultdict(dict)
    reference = defaultdict(dict)
    distinctWords = []
    offset = []

    for key in tqdm(sorted(data.keys())):
        docs = data[key]
        temp = []
        
        for i in range(len(docs)):
            posting = docs[i]
            docID = re.sub(r'.*d([0-9]*).*', r'\1', posting)
            
            temp = re.sub(r'.*t([0-9]*).*', r'\1', posting)
            if temp != posting:
                title[key][docID] = float(temp)
            
            temp = re.sub(r'.*b([0-9]*).*', r'\1', posting)
            if temp != posting:
                body[key][docID] = float(temp)

            temp = re.sub(r'.*i([0-9]*).*', r'\1', posting)
            if temp != posting:
                info[key][docID] = float(temp)

            temp = re.sub(r'.*c([0-9]*).*', r'\1', posting)
            if temp != posting:
                category[key][docID] = float(temp)

            temp = re.sub(r'.*l([0-9]*).*', r'\1', posting)
            if temp != posting:
                link[key][docID] = float(temp)
            
            temp = re.sub(r'.*r([0-9]*).*', r'\1', posting)
            if temp != posting:
                reference[key][docID] = float(temp)

        string = key + ' ' + str(finalCount) + ' ' + str(len(docs))
        distinctWords.append(string)
        offset.append(str(offsetSize))
        offsetSize += len(string) + 1

    titleData = []
    titleOffset = []
    prevTitle = 0

    bodyData = []
    bodyOffset = []
    prevBody = 0
    
    infoData = []
    infoOffset = []
    prevInfo = 0
    
    linkData = []
    linkOffset = []
    prevLink = 0
    
    categoryData = []
    categoryOffset = []
    prevCategory = 0
    
    referenceOffset = []
    referenceData = []
    prevReference = 0

    for key in tqdm(sorted(data.keys())):

        if key in title:
            string = key + ' '
            docs = title[key]
            docs = sorted(docs, key = docs.get, reverse=True)
            for doc in docs:
                string += doc + ' ' + str(title[key][doc]) + ' '
            titleOffset.append(str(prevTitle) + ' ' + str(len(docs)))
            prevTitle += len(string) + 1
            titleData.append(string)

        if key in body:
            string = key + ' '
            docs = body[key]
            docs = sorted(docs, key = docs.get, reverse=True)
            for doc in docs:
                string += doc + ' ' + str(body[key][doc]) + ' '
            bodyOffset.append(str(prevBody) + ' ' + str(len(docs)))
            prevBody += len(string) + 1
            bodyData.append(string)

        if key in info:
            string = key + ' '
            docs = info[key]
            docs = sorted(docs, key = docs.get, reverse=True)
            for doc in docs:
                string += doc + ' ' + str(info[key][doc]) + ' '
            infoOffset.append(str(prevInfo) + ' ' + str(len(docs)))
            prevInfo += len(string) + 1
            infoData.append(string)

        if key in category:
            string = key + ' '
            docs = category[key]
            docs = sorted(docs, key = docs.get, reverse=True)
            for doc in docs:
                string += doc + ' ' + str(category[key][doc]) + ' '
            categoryOffset.append(str(prevCategory) + ' ' + str(len(docs)))
            prevCategory += len(string) + 1
            categoryData.append(string)

        if key in link:
            string = key + ' '
            docs = link[key]
            docs = sorted(docs, key = docs.get, reverse=True)
            for doc in docs:
                string += doc + ' ' + str(link[key][doc]) + ' '
            linkOffset.append(str(prevLink) + ' ' + str(len(docs)))
            prevLink += len(string) + 1
            linkData.append(string)

        if key in reference:
            string = key + ' '
            docs = reference[key]
            docs = sorted(docs, key = docs.get, reverse=True)
            for doc in docs:
                string += doc + ' ' + str(reference[key][doc]) + ' '
            referenceOffset.append(str(prevReference) + ' ' + str(len(docs)))
            prevReference += len(string) + 1
            referenceData.append(string)

    thread = []
    
    thread.append(writeThread('t', titleData, titleOffset, finalCount))
    thread.append(writeThread('b', bodyData, bodyOffset, finalCount))
    thread.append(writeThread('i', infoData, infoOffset, finalCount))
    thread.append(writeThread('c', categoryData, categoryOffset, finalCount))
    thread.append(writeThread('l', linkData, linkOffset, finalCount))
    thread.append(writeThread('r', referenceData, referenceOffset, finalCount))

    for i in range(6):
        thread[i].start()

    for i in range(6):
        thread[i].join()

    with open('../data/vocab.txt', 'a') as f:
        f.write('\n'.join(distinctWords))
        f.write('\n')

    with open('../data/offset.txt', 'a') as f:
        f.write('\n'.join(offset))
        f.write('\n')

    return finalCount+1, offsetSize


def mergeFiles(fileCount):

    words = {}
    files = {}
    top = {}
    flag = [0] * fileCount
    data = defaultdict(list)
    heap = []
    finalCount = 0
    offsetSize = 0

    for i in range(fileCount):
        filename = '../data4/index' + str(i) + '.txt'
        files[i] = open(filename, 'r')
        flag[i] = 1
        top[i] = files[i].readline().strip()
        words[i] = top[i].split()
        if words[i][0] not in heap:
            heapq.heappush(heap, words[i][0])

    count = 0
    while any(flag) == 1:
        temp = heapq.heappop(heap)
        count += 1
        print(count)
        if count%100000 == 0:
            oldFileCount = finalCount
            finalCount, offsetSize = writeFinalIndex(data, finalCount, offsetSize)
            if oldFileCount != finalCount:
                data = defaultdict(list)
        for i in range(fileCount):
            if flag[i]:
                if words[i][0] == temp:
                    data[temp].extend(words[i][1:])
                    top[i] = files[i].readline().strip()
                    if top[i] == '':
                        flag[i] = 0
                        files[i].close()
                        #os.remove('../data/index' + str(i) + '.txt')
                    else:
                        words[i] = top[i].split()
                        if words[i][0] not in heap:
                            heapq.heappush(heap, words[i][0])
                        
    finalCount, offsetSize = writeFinalIndex(data, finalCount, offsetSize)


def writeIntoFile(index, dictID, fileCount, titleOffset):

    prevTitleOffset = titleOffset
    data = []
    for key in sorted(index.keys()):
        string = key + ' '
        postings = index[key]
        string += ' '.join(postings)
        data.append(string)

    filename = '../data/index' + str(fileCount) + '.txt'
    with open(filename, 'w') as f:
        f.write('\n'.join(data))

    data = []
    dataOffset = []
    for key in sorted(dictID):
        temp = str(key) + ' ' + dictID[key].strip()
        data.append(temp)
        dataOffset.append(str(prevTitleOffset))
        prevTitleOffset += len(temp) + 1

    filename = '../data/title.txt'
    with open(filename, 'a') as f:
        f.write('\n'.join(data))
        f.write('\n')
    
    filename = '../data/titleOffset.txt'
    with open(filename, 'a') as f:
        f.write('\n'.join(dataOffset))
        f.write('\n')

    return prevTitleOffset


class DocHandler(xml.sax.ContentHandler):

    def __init__(self):
        
        self.CurrentData = ''
        self.title = ''
        self.text = ''
        self.ID = ''
        self.idFlag = 0


    def startElement(self, tag, attributes):

        self.CurrentData = tag
        if tag == 'page':
            print(pageCount)
            

    def endElement(self, tag):
       
        if tag == 'page':
            d = Doc()
            dictID[pageCount] = self.title.strip().encode("ascii", errors="ignore").decode()
            title, body, info, categories, links, references = d.processText(pageCount, self.text, self.title)
            i = Indexer( title, body, info, categories, links, references)
            i.createIndex()
            self.CurrentData = ''
            self.title = ''
            self.text = ''
            self.ID = ''
            self.idFlag = 0


    def characters(self, content):

        if self.CurrentData == 'title':
            self.title += content
        elif self.CurrentData == 'text':
            self.text += content
        elif self.CurrentData == 'id' and self.idFlag == 0:
            self.ID = content
            self.idFlag = 1


class Parser():

    def __init__(self, filename):

        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, 0)
        self.handler = DocHandler()
        self.parser.setContentHandler(self.handler)
        self.parser.parse(filename)

if __name__ == '__main__':

    parser = Parser(sys.argv[1])
    with open('../data/fileNumbers.txt', 'w') as f:
        f.write(str(pageCount))
   
    offset = writeIntoFile(indexMap, dictID, fileCount, offset)
    indexMap = defaultdict(list)
    dictID = {}
    fileCount += 1
    mergeFiles(fileCount)
