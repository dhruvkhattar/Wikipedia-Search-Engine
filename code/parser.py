import pdb
import xml.sax

class DocHandler(xml.sax.ContentHandler):

    def __init__(self):
        
        self.CurrentData = ''
        self.title = ''
        self.reTitle = ''
        self.text = ''
        self.ID = ''
        self.count = 0
        self.idFlag = 0


    def startElement(self, tag, attributes):

        self.CurrentData = tag
        if tag == 'page':
            pdb.set_trace()
            self.count += 1
        elif tag == 'redirect':
            print 'Redirect:', attributes['title']


    def endElement(self, tag):
        
        if self.CurrentData == 'title':
            print 'Title:', self.title
        elif self.CurrentData == 'text':
            print 'Text:', self.text
        elif self.CurrentData == 'id':
            print 'ID:', self.ID
        if tag == 'page':
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

    def __init__(self):

        self.parser = xml.sax.make_parser()
        self.parser.setFeature(xml.sax.handler.feature_namespaces, 0)
        Handler = DocHandler()
        self.parser.setContentHandler(Handler)
        self.parser.parse('../data/wiki-search-small.xml')

if __name__ == '__main__':

    parser = Parser()
