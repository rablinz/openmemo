# -*- coding: utf-8 -*-

import logging
from openmemo.tests.tools import *
from openmemo.conversion.formats.base import Importer
from openmemo.conversion.exceptions import  ConversionFailure
import openmemo.tests.tools.model as m
from fs.tempfs import TempFS

logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.DEBUG)

class TestImporter (TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.fs = TempFS()
        self.importer = Importer()
        
    def test_finds_index_file_in_a_subdirectory(self):
        self.fs.makedir("directory")
        self.fs.setcontents("directory/file.txt", "test")
        index_file = self.importer._find_index_file(self.fs, ["*.txt"])
        assert_equals("directory/file.txt", index_file)
 
