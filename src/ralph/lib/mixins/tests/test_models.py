# -*- coding: utf-8 -*-
from django.test import TestCase

from ralph.tests.models import Foo


class AdminUrlTestCase(TestCase):
    def test_returned_url(self):
        obj = Foo.objects.create(bar='test')
        self.assertEqual(
            '/tests/foo/{}/change/'.format(obj.pk), obj.get_absolute_url()
        )
