from __future__ import with_statement

import ast
import os

from django.test import TestCase
from .base import TESTS_ROOT
from ..parsers import Parser


class ParserTests(TestCase):

    def setUp(self):
        self.example_project = os.path.join(TESTS_ROOT, 'example_project')
        self.filepath_list = [
            '__init__.py',
            'app/__init__.py',
            'app/admin.py',
            'app/forms.py',
            'app/models.py',
            'app/tests.py',
            'app/urls.py',
            'app/views.py',
            'bad_code.py',
            'good_code.py',
            'syntax_error.py',
        ]

    def test_init_with_absolute_path(self):
        parser = Parser(self.example_project)
        self.assertEqual(parser.source, self.example_project)

    def test_init_with_relative_path(self):
        with self.assertRaises(ValueError):
            parser = Parser('relative/path')

    def test_walk(self):
        parser = Parser(self.example_project)
        self.assertItemsEqual(
            parser.walk(),
            [os.path.join(self.example_project, x) for x in self.filepath_list]
        )

    def test_relpath(self):
        parser = Parser(self.example_project)
        path = os.path.join(self.example_project, 'app/models.py')
        self.assertEqual(parser.relpath(path), 'app/models.py')

    def test_parse_file(self):
        parser = Parser(self.example_project)
        path = os.path.join(self.example_project, 'app/models.py')
        code = parser.parse_file(path)
        self.assertIsInstance(code, tuple)
        self.assertIsInstance(code[1], ast.Module)
        self.assertEqual(code[0], 'app/models.py')

    def test_parse_file_with_syntax_error(self):
        parser = Parser(self.example_project)
        path = os.path.join(self.example_project, 'syntax_error.py')
        code = parser.parse_file(path)
        self.assertIsInstance(code, tuple)

    def test_parse_non_existent_file(self):
        parser = Parser(self.example_project)
        path = os.path.join(self.example_project, 'non_existent.py')
        with self.assertRaises(IOError):
            code = parser.parse_file(path)

    def test_parse(self):
        parser = Parser(self.example_project)
        code = parser.parse()
        self.assertIsInstance(code, dict)
        self.assertItemsEqual(parser.parse(), self.filepath_list)
