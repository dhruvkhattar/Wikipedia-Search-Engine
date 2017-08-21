import re
import pdb
import xml.sax
from nltk.corpus import stopwords
from nltk.stem.porter import *

stopWords = set(stopwords.words('english'))
stemmer = PorterStemmer()

class Doc():

    def __init__(self):

        pass
        
    
    def tokenize(self, data):

        data = re.sub(r'http[^\ ]*\ ', r' ', data) # removing urls
        data = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', data) # removing html entities
        data = re.sub(r'\||\.|\*|\[|\]|\:|\;|\,|\{|\}|\(|\)|\=|\+|\-|\_|\#|\!|\`|\"|\?|\/|\>|\<|\&|\\|\u2013|\n', r' ', data) # removing special characters
        data = data.split()
        return data

    
    def removeStopWords(self, data):
        
        return [w for w in data if not w in stopWords]


    def stem(self, data):
        
        return map(lambda x: stemmer.stem(x), data)


    def processText(self, ID, text, title):
        
        text = text.lower() #Case Folding
        references = self.extractReferences(text)
        links = self.extractExternalLinks(text)
        categories = self.extractCategories(text)
        info = self.extractInfobox(text)
        body = self.extractBody(text)
        title = self.extractTitle(title.lower())

        return (title, body, info, categories, links, references)

    def extractTitle(self, text):

        data = self.tokenize(text)
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data


    def extractBody(self, text):

        data = text.split('==references==')
        if len(data) == 1:
            data = text.split('== references == ')
        data = re.sub(r'\{\{.*\}\}', r' ', data[0])
        
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

        data = text.split('== references ==')
        if len(data) == 1:
            data = text.split('==references==')
            if len(data) == 1:
                return []
        data = data[1].split('\n')
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
        
        data = text.split('==external links==')
        if len(data) == 1: #No external links
            return []
        data = data[1].split('\n')
        links = []
        for line in data:
            if re.match(r'\*[\ ]*\[', line):
                links.append(line)
        
        data = self.tokenize(' '.join(links))
        data = self.removeStopWords(data)
        data = self.stem(data)
        return data
                 

class DocHandler(xml.sax.ContentHandler):

    def __init__(self):
        
        self.CurrentData = ''
        self.title = ''
        self.redirect = ''
        self.text = ''
        self.ID = ''
        self.count = 0
        self.idFlag = 0
        self.docs = []


    def startElement(self, tag, attributes):

        self.CurrentData = tag
        if tag == 'page':
            self.count += 1
            print(self.count)
        elif tag == 'redirect':
            self.redirect = attributes['title']
            

    def endElement(self, tag):
       
        if tag == 'page':
            d = Doc()
            self.docs.append(d.processText(self.ID, self.title, self.text))
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
        Handler = DocHandler()
        self.parser.setContentHandler(Handler)
        self.parser.parse(filename)
        pdb.set_trace()

if __name__ == '__main__':

    parser = Parser('../data/wiki-search-small.xml')
