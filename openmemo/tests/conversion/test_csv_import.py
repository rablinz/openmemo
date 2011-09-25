# -*- coding: utf-8 -*-

import logging
from openmemo.tests.tools import *
from openmemo.conversion.formats import CSVImporter
from openmemo.conversion.exceptions import  ConversionFailure
import openmemo.tests.tools.model as m
from fs.tempfs import TempFS
from os.path import sep

logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.DEBUG)

class TestQAFromCSVImport (TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.fs = TempFS()
        factory = m.ImportedInstanceFactory(self, field_types={
            'question': 'html',
            'answer': 'html'
        })
        self.importer = CSVImporter(self.fs, factory, m.HTMLMarkupImporter(self))
        self.cos = []
        self.images = []
        self.sounds = []

    def test_single_card(self):
        data = u"question 1, answer 1"
        self.fs.setcontents('index.csv', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question 1", self.cos[0]['question'])
        assert_equals(u"answer 1", self.cos[0]['answer'])

    def test_multiple_cards(self):
        data = """question, answer\r\nquestion 2, answer 2"""
        self.fs.setcontents('index.csv', data)
        self.importer()
        assert_equals(2, len(self.cos))
        assert_equals(u"question", self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])
        assert_equals(u"question 2", self.cos[1]['question'])
        assert_equals(u"answer 2", self.cos[1]['answer'])

    def test_double_quotes(self):
        data = u"\"question , 1\", \"answer , 1\""
        self.fs.setcontents('index.csv', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question , 1", self.cos[0]['question'])
        assert_equals(u"answer , 1", self.cos[0]['answer'])

    def test_new_line_in_quoted_value(self):
        data = u"\"question \r\n, 1\", \"answer\r\n a , 1\""
        self.fs.setcontents('index.csv', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question \n, 1", self.cos[0]['question'])
        assert_equals(u"answer\n a , 1", self.cos[0]['answer'])

    def test_quote_character_can_be_escaped_by_backslash(self):
        data = u"question \\\" 1, \"answer\\\" 1\""
        self.fs.setcontents('index.csv', data)
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question \" 1", self.cos[0]['question'])
        assert_equals(u"answer\" 1", self.cos[0]['answer'])

    def test_custom_encoding(self):
        data = (u"być szczerym, to be frank").encode('cp1250')
        self.fs.setcontents('index.csv', data)
        self.importer.encoding = 'cp1250'
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"być szczerym", self.cos[0]['question'])
        assert_equals(u"to be frank", self.cos[0]['answer'])

    def test_custom_delimiter(self):
        data = u"question , 1; answer , 1"
        self.fs.setcontents('index.csv', data)
        self.importer.delimiter = ';'
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"question , 1", self.cos[0]['question'])
        assert_equals(u"answer , 1", self.cos[0]['answer'])

    def test_card_with_image(self):
        data = u'<img src="image.jpg" />, answer'
        self.fs.setcontents('index.csv', data)
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
        data = u'<img src="image.jpg" />, answer'
        self.fs.makedir('dir')
        self.fs.setcontents('dir/index.csv', data)
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
        data = u'<span class="audio autoplay"><a href="button.mp3" /></span>, answer'
        self.fs.setcontents('index.csv', data)

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

    def test_image_in_subdir(self):
        data = u'<img src="myimages/here/image.jpg" />, answer'
        self.fs.setcontents('index.csv', data)

        self.fs.makedir('myimages')
        self.fs.opendir('myimages').makedir('here')
        self.fs.setcontents('myimages/here/image.jpg', self.data.getcontents('small.jpg'))
        self.importer()

        assert_equals(1, len(self.cos))
        assert_equals(u'<img src="/images/image.jpg"/>', self.cos[0]['question'])
        assert_equals(u"answer", self.cos[0]['answer'])

    def test_byte_order_mark_in_utf8_files_is_removed(self):
        data = u'\ufeff\uac00\uac8c, store'
        self.fs.setcontents('index.csv', data.encode('utf8'))
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"\uac00\uac8c", self.cos[0]['question'])
        assert_equals(u"store", self.cos[0]['answer'])

    def test_invalid_xml_results_in_failure(self):
        data = u'<b>question, answeer'
        self.fs.setcontents('index.csv', data)
        assert_raises(ConversionFailure, self.importer)

    def test_invalid_fields_number_results_in_failure(self):
        data = u'question'
        self.fs.setcontents('index.csv', data)
        assert_raises(ConversionFailure, self.importer)

    def test_not_existing_image_results_in_failure(self):
        data = u'<img src="myimages/here/image.jpg" />, answer'
        self.fs.setcontents('index.csv', data)
        try:
            self.importer()
            fail()
        except ConversionFailure, e:
            print e
            assert_true("myimages/here/image.jpg" in unicode(e).replace(sep, "/"))

    def test_field_names_can_be_passed_as_param(self):
        data = u"a 1, b 1, c 1"
        self.fs.setcontents('index.csv', data)
        self.importer.fields = ['word', 'pronunciation', 'translation']
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"a 1", self.cos[0]['word'])
        assert_equals(u"b 1", self.cos[0]['pronunciation'])
        assert_equals(u"c 1", self.cos[0]['translation'])

    def test_field_names_can_be_loaded_from_first_row(self):
        data = u"word, pronunciation, translation\na 1, b 1, c 1"
        self.fs.setcontents('index.csv', data)
        self.importer.fields_in_first_row = True
        self.importer()
        assert_equals(1, len(self.cos))
        assert_equals(u"a 1", self.cos[0]['word'])
        assert_equals(u"b 1", self.cos[0]['pronunciation'])
        assert_equals(u"c 1", self.cos[0]['translation'])

    def test_image_paths_are_correct_when_index_in_subdirectory(self):
        factory = m.ImportedInstanceFactory(self, field_types={
            'img': 'image',
        })
        self.importer = CSVImporter(self.fs, factory, m.HTMLMarkupImporter(self))
        self.importer.fields = ['img']

        data = u'image.jpg'
        self.fs.makedir('dir')
        self.fs.setcontents('dir/index.csv', data)
        image_data = self.data.getcontents('small.jpg')
        self.fs.setcontents('dir/image.jpg', image_data)
        self.importer()

        assert_equals(1, len(self.cos))
        assert_equals(self.images[0], self.cos[0]['img'])

        assert_equals(1, len(self.images))
        assert_equals('image.jpg', self.images[0]['filename'])
        assert_equals('image/jpeg', self.images[0]['mime_type'])
        assert_true(image_data == self.images[0]['data'])

    def test_sound_paths_are_correct_when_index_in_subdirectory(self):
        factory = m.ImportedInstanceFactory(self, field_types={
            'img': 'sound',
        })
        self.importer = CSVImporter(self.fs, factory, m.HTMLMarkupImporter(self))
        self.importer.fields = ['img']

        data = u'button.mp3'
        self.fs.makedir('dir')
        self.fs.setcontents('dir/index.csv', data)
        image_data = self.data.getcontents('button.mp3')
        self.fs.setcontents('dir/button.mp3', image_data)
        self.importer()

        assert_equals(1, len(self.cos))
        assert_equals(self.sounds[0], self.cos[0]['img'])

        assert_equals(1, len(self.sounds))
        assert_equals('button.mp3', self.sounds[0]['filename'])
        assert_equals('audio/mpeg', self.sounds[0]['mime_type'])
        assert_true(image_data == self.sounds[0]['data'])
