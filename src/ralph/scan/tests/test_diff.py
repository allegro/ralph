# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.scan.diff import _find_database_key


class DiffTest(TestCase):

    def test_find_database_key(self):
        db_key = _find_database_key({
            ('database',): 123,
            ('some.plugin.name',): 123,
        })
        self.assertEqual(db_key, ('database',))
        db_key = _find_database_key({
            ('some.plugin_name',): 321,
            ('some.other.plugin.name', 'database'): 321,
        })
        self.assertEqual(db_key, ('some.other.plugin.name', 'database'))
        db_key = _find_database_key({
            ('some.plugin_name',): 321,
            ('some.other.plugin.name', 'db'): 321,
        })
        self.assertIsNone(db_key)
