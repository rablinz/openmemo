"""
Classes here defines a simple data model used for testing import and export.

Your application will probably use a custom implementation.


"""

from openmemo.utils import attrdict
import openmemo.conversion.model as base
from openmemo.conversion.html import HTMLConverter

class Entity (attrdict):
    pass

class ContentObject (Entity):
    pass

class Image (Entity):
    pass

class Sound (Entity):
    pass

base.ContentObject.register(ContentObject)
base.Image.register(Image)
base.Sound.register(Sound)

class ImportedInstanceFactory (object):
    def __init__(self, suite, field_types={}):
        self.suite = suite
        self.field_types = field_types
    
    def ContentObject(self, importer, data):
        types = self.field_types
        for k, v in data.iteritems():
            if k in types:
                method = getattr(importer, 'import_'+types[k])
                data[k] = method(v)
        co = ContentObject(**data) 
        self.suite.cos.append(co)
        return co

    def Image(self, importer, data):
        image = Image(**data)
        self.suite.images.append(image)
        return image

    def Sound(self, importer, data):
        sound = Sound(**data)
        self.suite.sounds.append(sound)
        return sound
       
from openmemo.conversion.html.tags import *
   
class HTMLMarkupImporter (HTMLConverter):
    def __init__(self, suite):
        tags = [
            Processor(XPath('//img'), ResourceReader('Image', 'src'), ResourceWriter('src', src=lambda o: '/images/'+o['filename'])),
            Processor(audio_locator, audio_reader, ResourceWriter('href', lambda o: '/sounds/'+o['filename']))               
        ]
        super(HTMLMarkupImporter, self).__init__(tags)  

class HTMLMarkupExporter (HTMLConverter):
    def __init__(self, suite):       
        self.suite = suite 
        tags = [Processor(XPath('//img'), self._read_img, self._write_img)]
        super(HTMLMarkupExporter, self).__init__(tags)
    
    def _read_img(self, imp, factory, dir, node):
        return [img for img in self.suite.images if img.filename == node.attrib['src']][0]

    def _write_img(self, img, dir, node, *args, **kwargs):
        node.attrib['src'] = 'images/'+img.filename+'.jpg' 
               


    


