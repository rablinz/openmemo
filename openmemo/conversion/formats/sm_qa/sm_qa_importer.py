from openmemo.conversion.exceptions import ConversionFailure
from codecs import EncodedFile
from ..base import Importer
from os.path import dirname

import logging
import os.path
log = logging.getLogger(__name__)

class SuperMemoQAImporter (Importer):
    encoding = 'utf_8_sig'
    filenames = ('*.txt',)
    fields = ('question', 'answer')
    
    def __init__(self, dir, factory, markup):
        self.dir = dir 
        self.factory = factory
        self.markup = markup 

    def __call__(self):
        index_file_path = self._find_index_file(self.dir, self.filenames)
        self.markup.dir = self.dir.opendir(dirname(index_file_path))
        self.markup.factory = self.factory  

        with EncodedFile(self.dir.open(index_file_path, 'rU'), 'utf8', self.encoding) as file:
            self._parse(file)

    def _parse(self, file):
        self._prev_state = None
        self._state = self._process_question
        self._question = ""
        self._answer = ""
        for line_no, line in enumerate(file):
            self._line = line.decode('utf8')
            self._line_no = line_no
            self._state()

        # if the last line was an answer, close the card    
        if self._state == self._process_answer: 
            self._change_state(self._save_card, execute=True)
        
        # have we end up with another state than after save?
        if not (self._state == self._process_question
                 and self._prev_state == self._save_card):
            raise ConversionFailure(
                "Illegal end state: %s" % self._state.__name__) 
            
            
    def _change_state(self, new_state, execute=False):
        self._prev_state = self._state
        self._state = new_state 
        if execute:
            self._state()
            
    def _process_question(self):       
        if self._line.startswith("A: "):
            # end of the question, start of an answer
            self._change_state(self._process_answer, execute=True)
            return
        
        if not self._line.startswith("Q: "):
            raise ConversionFailure(
                "A question line (#%(line_num)s) without the 'Q: ' prefix", 
                line_num=self._line_no+1)
        
        self._question += self._line[3:].rstrip() + "\n"
                
    def _process_answer(self):
        # empty line, end of the answer and of the card
        if self._line.strip() == "":
            self._change_state(self._save_card, execute=True)
            return
        
        if not self._line.startswith("A: "):
            raise ConversionFailure(
                "An answer line (#%(line_num)s) without the 'A: ' prefix", 
                    _line_no=self._line_no+1)
       
        self._answer += self._line[3:].rstrip() + "\n"
        
    def _save_card(self):
        question = self._question.rstrip()
        answer = self._answer.rstrip()
        self.factory.ContentObject(self, dict(zip(self.fields, (question, answer))))
        self._question = ""
        self._answer = ""

        self._change_state(self._process_question, execute=False)
       
    def import_html(self, value):
        return self.markup(self, value)                 
        
