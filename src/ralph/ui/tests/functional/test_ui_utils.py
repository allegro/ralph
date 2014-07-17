# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import Device
from ralph.ui.tests.global_utils import login_as_su


class TestUnlockField(TestCase):

    def setUp(self):
        self.client = login_as_su()

    def test_not_allowed_request(self):
        response = self.client.get('/ui/unlock-field/', follow=True)
        self.assertEqual(response.status_code, 405)

    def test_correct_request(self):
        # prepare sample device
        dev = Device(
            name='sample.dc',
            sn='sn123123123_1'
        )
        dev.dc = 'DC'
        dev.save(priority=215)

        # test it
        response = self.client.post(
            '/ui/unlock-field/',
            {
                'device': dev.pk,
                'field': 'dc'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        dev = Device.objects.get(pk=dev.pk)
        priorities = dev.get_save_priorities()
        self.assertEqual(priorities['dc'], 0)
