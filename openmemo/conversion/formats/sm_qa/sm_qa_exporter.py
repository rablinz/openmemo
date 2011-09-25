import openmemo.conversion.model as m
import codecs
import os

class SuperMemoQAExporter (object):
    
    encoding = 'utf8'
    line_terminator = '\r\n'
    index_file = 'cards.txt'
    
    def __init__(self, dst_dir):
        self.dst_dir = dst_dir

    def __call__(self, objects):
        encoder = codecs.getencoder(self.encoding)
        self._encode = lambda x: encoder(x)[0]

        self._file = self.dst_dir.open(self.index_file, 'wb')
        self._card_no = 0
        try:
            for object in objects:
                self._export_object(object)
        finally:
            self._file.close()

    def _export_object(self, o):
        if isinstance(o, m.ContentObject):
            self._export_qa(o)
    
    def _export_qa(self, card):
        question = u"".join([u"Q: "+line+self.line_terminator for line \
                            in card.question.splitlines()])
        answer = u"".join([u"A: "+line+self.line_terminator for line \
                          in card.answer.splitlines()])

        if self._card_no != 0:
            self._file.write(self.line_terminator)
        
        self._file.write(self._encode(question))
        self._file.write(self._encode(answer))

        self._card_no += 1
