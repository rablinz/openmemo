from openmemo.conversion.exceptions import ConversionFailure
import codecs
import csv
import logging
import os.path
from ...resources import resource_from_file
from ..base import Importer
log = logging.getLogger(__name__)

class CSVImporter (Importer):
    line_terminator = '\r\n'
    delimiter = ','
    filenames = ('*.csv', '*.tsv', '*.txt')
    encoding = 'utf_8_sig'
    escapechar = '\\'
    fields = ('question', 'answer')
    fields_in_first_row = False
    
    def __init__(self, dir, factory, markup):
        self.dir = dir
        self.factory = factory
        self.markup = markup

    def __call__(self):
        index_file_path = self._find_index_file(self.dir, self.filenames)
        self.index_dir = self.dir.opendir(os.path.dirname(index_file_path))  
        self.markup.dir = self.index_dir
        self.markup.factory = self.factory
            
        decoder = codecs.getdecoder(self.encoding)
        decode = lambda x: decoder(x)[0]

        parser_settings = dict(
            skipinitialspace=True, 
            escapechar=str(self.escapechar),
            lineterminator=str(self.line_terminator),
            delimiter=str(self.delimiter)
        )
        process = lambda f: decode(f).replace(self.line_terminator, "\n")       
        
        file = self.dir.open(index_file_path, 'rb')

        with file:
            reader = csv.reader(file, **parser_settings)
            lines = enumerate(reader)
            
            if self.fields_in_first_row:
                field_names = lines.next()[1]
            else:    
                field_names = self.fields         
            len_field_names = len(field_names)
            
            for line_num, fields in lines:
                field_num = len(fields)
                if field_num != len_field_names:
                    raise ConversionFailure("Expected %(expected_field_num)d values  per line, "
                                      "got %(actual_field_num)d at line %(line_num)s: %(fields)s",
                                      expected_field_num=len_field_names, 
                                      actual_field_num=field_num, line_num=line_num, fields=fields)
                fields = map(process, fields)
                values = dict(zip(field_names, fields))
                self.factory.ContentObject(self, values)

    def import_sound(self, value):
        if value: 
            data = resource_from_file(self.index_dir, value)
            return self.factory.Sound(self, data)
    
    def import_image(self, value):
        if value:
            data = resource_from_file(self.index_dir, value)
            return self.factory.Image(self, data)   
    
    def import_html(self, value):
        if value:
            return self.markup(self, value) 

        



