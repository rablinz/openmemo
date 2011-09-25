import logging
from ..resources import resource_from_file

log = logging.getLogger(__name__)

class Processor (object):
    def __init__(self, locator, reader, writer):
        self.locator = locator
        self.reader = reader
        self.writer = writer

    def __call__(self, importer, factory, dir, doc):
        for node in self.locator(doc):
            resource = self.reader(importer, factory, dir, node)
            self.writer(resource, dir, node)

class XPath (object):
    def __init__(self, xpath):
        self.xpath = xpath

    def __call__(self, doc):
        return doc.xpath(self.xpath)

class ResourceReader (object):
    def __init__(self, type, attr):
        self.type = type
        self.attr = attr

    def __call__(self, importer, factory, dir, node):
        path = node.attrib[self.attr]
        data = resource_from_file(dir, path)
        method = getattr(factory, self.type)
        resource = method(importer, data)
        return resource

class ResourceWriter (object):
    def __init__(self, attr=None, src=None):
        self.attr = attr
        self.src = src

    def __call__(self, resource, dir, node):
        node.attrib[self.attr] = self.src(resource)

audio_locator = XPath('//span[contains(@class, "audio")]/a')
audio_reader = ResourceReader('Sound', 'href')
audio_writer = ResourceWriter('href', lambda o: o['filename'])



