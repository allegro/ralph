# -*- coding: utf-8 -*-
"""Tests for special fields."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.forms import ValidationError
from django.test import TestCase

from ralph.ui.forms.addresses import IPWithHostField


class TestIPWithHostnameField(TestCase):
    """Tests for ``IPWithHostField``"""

    def test_field_invalid_when_ip_number_missing(self):
        with self.assertRaises(ValidationError):
            IPWithHostField().compress(['example.com', ''])
