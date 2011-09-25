# -*- coding: utf-8 -*-

from openmemo.tests.tools import *
from openmemo.conversion import ConversionFailure
from openmemo.conversion.formats.sm_qa import SuperMemoQAImporter
import openmemo.tests.tools.model as m
from fs.tempfs import TempFS

class TestSuperMemoQAImport (TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.fs = TempFS()
        factory = m.ImportedInstanceFactory(self, field_types={    
            'question': 'html',
            'answer': 'html'                                    
        })      
        self.importer = SuperMemoQAImporter(self.fs, factory, m.HTMLMarkupImporter(self))
        self.cos = []
        self.images = []
        self.sounds = []
 
    def test_single_card(self):
        data = u"Q: question 1\nA: answer 1"
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(unicode, type(self.cos[0]['question']))
        assert_equals(unicode, type(self.cos[0]['answer']))        
        assert_equals(u"question 1", self.cos[0]['question'])
        assert_equals(u"answer 1", self.cos[0]['answer'])
        
    def test_windows_line_endings(self):
        data = u"Q: question 1\r\nA: answer 1"
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question 1", self.cos[0]['question'])
        assert_equals(u"answer 1", self.cos[0]['answer'])
        
    def test_multiple_cards(self):
        data = """Q: question
A: answer

Q: question 2
A: answer 2"""
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(2, len(self.cos))
        assert_equals(u"question", self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])
        assert_equals(u"question 2", self.cos[1]['question'])
        assert_equals(u"answer 2", self.cos[1]['answer'])
        
    def test_content_is_right_trimmed(self):
        data = u"Q: question   \nA: answer   \n"
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question", self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])            
 
    def test_multiline_question_and_answer(self):
        data = """Q: question
Q: end of question
A: answer
A: end of answer"""
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question\nend of question", self.cos[0]['question'])
        assert_equals(u"answer\nend of answer", self.cos[0]['answer'])            
        
    def test_multiline_question_and_answer_lines_are_rtrimmed(self):
        data = "Q: question  \nQ: end of question  \nA: answer  \nA: end of answer  "
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question\nend of question", self.cos[0]['question'])
        assert_equals(u"answer\nend of answer", self.cos[0]['answer'])            
 
    def test_custom_encoding(self):
        data = (u"Q: być szczerym\nA: to be frank").encode('cp1250')
        self.fs.setcontents('cards.txt', data)
        self.importer.encoding = 'cp1250'
        self.importer()        
        assert_equals(1, len(self.cos))
        assert_equals(unicode, type(self.cos[0]['question']))
        assert_equals(unicode, type(self.cos[0]['answer']))
        assert_equals(u"być szczerym", self.cos[0]['question'])
        assert_equals(u"to be frank", self.cos[0]['answer']) 
               
    def test_html_tags_are_preserved(self):
        data = """Q: hist: When did we <b>land on the moon</b>?
A: 1969 <i>(July 20)</i>"""
        self.fs.setcontents('cards.txt', data)
        self.importer()
        assert_equals(u"hist: When did we <b>land on the moon</b>?", self.cos[0]['question'])
        assert_equals(u"1969 <i>(July 20)</i>", self.cos[0]['answer'])
        
    def test_card_with_image(self):
        data = u"""Q: <img src="image.jpg" />
A: answer"""
        self.fs.setcontents('index.txt', data)
        image_data = self.data.getcontents('small.jpg')
        self.fs.setcontents('image.jpg', image_data)
        self.importer()

        assert_equals(1, len(self.cos))
        assert_equals(u'<img src="/images/image.jpg"/>', self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])

        assert_equals(1, len(self.images))
        assert_equals('image.jpg', self.images[0]['filename'])
        assert_equals('image/jpeg', self.images[0]['mime_type'])
        assert_true(image_data == self.images[0]['data'])
        
    def test_card_with_index_in_subdirectory_and_image(self):
        data = u'Q: <img src="image.jpg" />\nA: answer'
        self.fs.makedir('dir')
        self.fs.setcontents('dir/index.txt', data)
        image_data = self.data.getcontents('small.jpg')
        self.fs.setcontents('dir/image.jpg', image_data)
        self.importer()

        assert_equals(1, len(self.cos))
        assert_equals(u'<img src="/images/image.jpg"/>', self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])

        assert_equals(1, len(self.images))
        assert_equals('image.jpg', self.images[0]['filename'])
        assert_equals('image/jpeg', self.images[0]['mime_type'])
        assert_true(image_data == self.images[0]['data'])     
        
    def test_card_with_audio(self):
        data = u"""Q: <span class="audio autoplay"><a href="button.mp3" /></span>
A: answer"""
        self.fs.setcontents('index.txt', data)
                
        sound_data = self.data.getcontents('button.mp3')
        self.fs.setcontents('button.mp3', sound_data)

        self.importer()

        assert_equals(1, len(self.cos))
        assert_equals(u'<span class="audio autoplay"><a href="/sounds/button.mp3"/></span>', self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])

        assert_equals(1, len(self.sounds))
        assert_equals('button.mp3', self.sounds[0]['filename'])
        assert_equals('audio/mpeg', self.sounds[0]['mime_type'])
        assert_true(sound_data == self.sounds[0]['data'])
                       
    def test_byte_order_mark_in_utf8_files_is_removed(self):
        data = u'\ufeffQ: \uac00\uac8c\r\nA: store'
        self.fs.setcontents('index.txt', data.encode('utf8'))
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"\uac00\uac8c", self.cos[0]['question'])
        assert_equals(u"store", self.cos[0]['answer'])   
        
    def test_invalid_xml_results_in_input_error(self):
        data = u'Q: <b>question\nA: answer'
        self.fs.setcontents('index.txt', data)
        assert_raises(ConversionFailure, self.importer)        
        
    def test_invalid_fields_number_in_input_error(self):
        data = u'Q: question'
        self.fs.setcontents('index.txt', data)
        assert_raises(ConversionFailure, self.importer)                                