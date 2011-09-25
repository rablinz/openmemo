# -*- coding: utf-8 -*-

from openmemo.tests.tools import *
from openmemo.conversion.formats.csv import CSVExporter
import openmemo.tests.tools.model as m
from fs.tempfs import TempFS

class TestCSVExport (TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.fs = TempFS()
        self.exporter = CSVExporter(self.fs, m.HTMLMarkupExporter(self))
        
    def test_single_card(self):
        card = m.ContentObject()
        card['question'] = u'Question'
        card['answer'] = u'Answer'
        self.exporter([card])
        expected = '"Question","Answer"\r\n'
        assert_equals(expected, self.fs.getcontents('index.csv'))

    def test_multiple_cards(self):
        card = m.ContentObject()
        card['question'] = u'Question'
        card['answer'] = u'Answer'
        card2 = m.ContentObject()
        card2['question'] = u'Question 2'
        card2['answer'] = u'Answer 2'
        self.exporter([card, card2])
        expected = '"Question","Answer"\r\n"Question 2","Answer 2"\r\n'
        assert_equals(expected, self.fs.getcontents('index.csv'))
        
    def test_multiline_question_and_answer(self):
        card = m.ContentObject()
        card['question'] = u"Question\nend of question"
        card['answer'] = u"Answer\nend of answer"
        self.exporter([card])
        expected = '"Question\r\nend of question","Answer\r\nend of answer"\r\n'
        assert_equals(expected, self.fs.getcontents('index.csv'))              

    def test_custom_encoding(self):
        card = m.ContentObject()
        card['question'] = u"chrząszcz brzmi w trzcinie"
        card['answer'] =  u"zażółć gęślą jaźń"
        self.exporter.encoding = 'cp1250'
        self.exporter([card])
        expected = u'"chrząszcz brzmi w trzcinie","zażółć gęślą jaźń"\r\n'.encode('cp1250')
        assert_equals(expected, self.fs.getcontents('index.csv'))
        
    def test_card_with_image(self):
        self.images = [m.Image(filename='img2'), m.Image(filename='img1')]
        card = m.ContentObject()
        card['question'] = u'Question <img src="img2" />'
        card['answer'] = u'Answer <img src="img1" />'
        self.exporter([card])
        expected = '"Question <img src=""images/img2.jpg""/>","Answer <img src=""images/img1.jpg""/>"\r\n'
        assert_equals(expected, self.fs.getcontents('index.csv'))                  
