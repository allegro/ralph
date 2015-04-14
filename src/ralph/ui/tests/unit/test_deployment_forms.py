# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.forms import ValidationError
from django.test import TestCase

from ralph.ui.forms.deployment import (
    _validate_cols_count
)


class ValidateColsCountTest(TestCase):
    def test_correct_data(self):
        self.assertEqual(
            _validate_cols_count(3, [1, 2, 3], 0),
            None
        )
        self.assertEqual(
            _validate_cols_count(3, [1, 2, 3], 0, 1),
            None
        )
        self.assertEqual(
            _validate_cols_count(3, [1, 2, 3, 4], 0, 1),
            None
        )

    def test_incorrect_data(self):
        with self.assertRaises(ValidationError) as cm:
            _validate_cols_count(5, [1, 2, 3], 100)
        self.assertEqual(
            cm.exception.messages[0],
            "Incorrect number of columns (got 3, expected 5) at row 100"
        )
        with self.assertRaises(ValidationError) as cm:
            _validate_cols_count(5, [1, 2, 3, 4, 5, 6, 7, 8], 101, 2)
        self.assertEqual(
            cm.exception.messages[0],
            "Incorrect number of columns (got 8, expected 5 or 7) at row 101"
        )
        with self.assertRaises(ValidationError) as cm:
            _validate_cols_count(5, [1, 2, 3, 4], 102, 2)
        self.assertEqual(
            cm.exception.messages[0],
            "Incorrect number of columns (got 4, expected 5 or 7) at row 102"
        )
