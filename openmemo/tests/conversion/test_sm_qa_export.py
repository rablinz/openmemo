# -*- coding: utf-8 -*-

from openmemo.tests.tools import *
from openmemo.conversion.formats.sm_qa import SuperMemoQAExporter
import openmemo.tests.tools.model as m
import os
from fs.tempfs import TempFS

class TestSuperMemoQAExport (TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.fs = TempFS()
        self.exporter = SuperMemoQAExporter(self.fs)
        self.exporter.index_file = 'out.txt'        
 
    def test_single_card(self):
        card = m.ContentObject()
        card['question'] = u'Question'
        card['answer'] = u'Answer'
        self.exporter([card])
        expected = "Q: Question\r\nA: Answer\r\n"
        assert_equals(expected, self.fs.getcontents('out.txt'))

    def test_multiple_cards(self):
        card = m.ContentObject()
        card['question'] = u'Question'
        card['answer'] = u'Answer'
        card2 = m.ContentObject()
        card2['question'] = u'Question 2'
        card2['answer'] = u'Answer 2'
        self.exporter([card, card2])
        expected = "Q: Question\r\nA: Answer\r\n\r\nQ: Question 2\r\nA: Answer 2\r\n"
        assert_equals(expected, self.fs.getcontents('out.txt'))
        
    def test_multiline_question_and_answer(self):
        card = m.ContentObject()
        card['question'] = u"Question\nend of question"
        card['answer'] = u"Answer\nend of answer"
        self.exporter([card])
        expected = "Q: Question\r\nQ: end of question\r\nA: Answer\r\nA: end of answer\r\n"
        assert_equals(expected, self.fs.getcontents('out.txt'))             

    def test_custom_encoding(self):
        card = m.ContentObject()
        card['question'] = u"chrząszcz brzmi w trzcinie"
        card['answer'] =  u"zażółć gęślą jaźń"
        self.exporter.encoding = 'cp1250'
        self.exporter([card])
        expected = u'Q: chrząszcz brzmi w trzcinie\r\nA: zażółć gęślą jaźń\r\n'.encode('cp1250')
        assert_equals(expected, self.fs.getcontents('out.txt'))              
