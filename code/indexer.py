import sys
import operator
from collections import defaultdict
import timeit
import re
import pdb
import xml.sax
from nltk.corpus import stopwords
from nltk.stem.porter import *
import Stemmer

stemmer = Stemmer.Stemmer('english')
#stemmer = PorterStemmer()

stopWords = set(stopwords.words('english'))
stop_dict = defaultdict(int)
for word in stopWords:
    stop_dict[word] = 1

indexMap = {}

class Doc():

    def __init__(self):

        pass


    def tokenize(self, data):

        #data = re.sub(r'[^a-z0-9 ]',' ', data)
        data = re.findall("[\d]+|[\w]+", data)
        #data = re.sub(r'http[^\ ]*\ ', r' ', data) # removing urls
        #data = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', data) # removing html entities
        #data = re.sub(r'\'\||\.|\*|\[|\]|\:|\;|\,|\{|\}|\(|\)|\=|\+|\-|\_|\#|\!|\`|\"|\?|\/|\>|\<|\&|\\|\u2013|\n', r' ', data) # removing special characters
        return data

    
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
        
        words = defaultdict(int)
        d = defaultdict(int)
        for word in title:
            d[word] += 1
            words[word] += 1
        title = d
        
        d = defaultdict(int)
        for word in body:
            d[word] += 1
            words[word] += 1
        body = d

        d = defaultdict(int)
        for word in info:
            d[word] += 1
            words[word] += 1
        info = d
	
        d = defaultdict(int)
        for word in categories:
            d[word] += 1
            words[word] += 1
        categories = d
        
        d = defaultdict(int)
        for word in links:
            d[word] += 1
            words[word] += 1
        links = d
        
        d = defaultdict(int)
        for word in references:
            d[word] += 1
            words[word] += 1
        references = d
    
        for word in words.keys():
            if word not in indexMap:
                indexMap[word]= []
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

            indexMap[word].append((string, words[word]))


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


class DocHandler(xml.sax.ContentHandler):

    def __init__(self):
        
        self.CurrentData = ''
        self.title = ''
        self.text = ''
        self.ID = ''
        self.count = 0
        self.idFlag = 0


    def startElement(self, tag, attributes):

        self.CurrentData = tag
        if tag == 'page':
            self.count += 1
            print(self.count)
            

    def endElement(self, tag):
       
        if tag == 'page':
            d = Doc()
            d.processText(self.ID, self.text, self.title)
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
    start = timeit.default_timer()
    parser = Parser(sys.argv[1])
    with open(sys.argv[2], 'w') as fp:
        words = sorted(indexMap.keys())
        for word in words:
            indexMap[word].sort(key=operator.itemgetter(1), reverse=True)
            fp.write(word + ' - ')
            for each in indexMap[word]:
                fp.write(each[0] + ' ')
            fp.write('\n')
    fp.close()
    end = timeit.default_timer()
    print(end-start)
