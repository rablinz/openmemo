import cgi
#import xml.etree.cElementTree as etree
import lxml.etree as etree 
import mimetypes
import os
from ..exceptions import ConversionFailure

class HTMLConverter (object):
    """ Converts one markup to another, HTML-based
    
    One application might use <audio src="file.mp3">, another one <a href="file.mp3">.
    Every application uses its own values of 'src' attribute for <img>.
    This class is used for processing tags.
    
    """
    
    def __init__(self, processors=None, factory=None):
        """
        Arguments:
        processors - list of callables (usually instances of openmemo.conversion.base.tags.Tag)
        """ 
        super(HTMLConverter, self).__init__()
        self.processors = processors or []
        self.factory = factory
        self.dir = None
    
    def __call__(self, importer, html):
        """ Converts input HTML to output HTML using processors. 
        
        dir - current working directory, links in HTML are relative to it.
        """
        try:
            doc = etree.fromstring('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                               '<root>'+html.encode('utf8')+'</root>')
        except etree.XMLSyntaxError, e:
            raise ConversionFailure("Invalid XML: '%(xml)s'", xml=html)
        
        for processor in self.processors:
            processor(importer, self.factory, self.dir, doc)
        
        #xml = etree.tostring(doc, 'utf8')
        xml = etree.tounicode(doc)
        i = xml.find('<root>') + 6
        j = xml.rfind('</root>')
        xml = xml[i:j] #.decode('utf8')
        assert isinstance(xml, unicode)
        return xml
    
          
        

    
    
        
    
    
      
    
    
        
        
        