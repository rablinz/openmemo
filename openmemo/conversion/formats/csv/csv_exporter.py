import codecs
import csv
import openmemo.conversion.model as m
import os

class CSVExporter (object):
    
    index_file = 'index.csv'
    encoding = 'utf8'
    line_terminator = '\r\n'
    quoting = csv.QUOTE_ALL
    escapechar = '\\'
    doublequote = True  
    
    def __init__(self, dir, markup):
        self.dir = dir
        self.markup = markup  
    
    def __call__(self, objects):
        self.markup.dir = self.dir
        with self.dir.open(self.index_file, 'wb') as file:
            self._writer = csv.writer(file, quoting = self.quoting,
                                      lineterminator = self.line_terminator,
                                      escapechar = self.escapechar,
                                      doublequote = self.doublequote)
            for o in objects:
                self._export_object(o)

    def _export_object(self, o):
        if isinstance(o, m.ContentObject):
            self._export_qa(o)
            
    def _export_qa(self, card):
        question = self.markup(self, card.question)
        answer = self.markup(self, card.answer)  
        row = [question, answer]
        row = [s.encode(self.encoding).replace("\n", self.line_terminator) for s in row]
        self._writer.writerow(row)
        
        
        

        
