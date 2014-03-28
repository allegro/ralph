# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import skip

from django.test import TestCase
from powerdns.models import Record, Domain
from django.contrib.auth.models import User

from ralph.dnsedit.models import DNSHistory


class DNSHistoryTest(TestCase):

    def setUp(self):
        self.domain = Domain(name='example.com')
        self.domain.save()
        self.user = User.objects.create_user('user', 'user@example.com',
                                             'password')

    def tearDown(self):
        self.domain.delete()
        self.user.delete()

    @skip("Broken signals not being called")
    def test_record_create(self):
        record = Record(
            name='hostname.example.com',
            type='A',
            content='127.0.0.1',
            domain=self.domain,
        )
        record.saving_user = self.user
        record.save()
        history = DNSHistory.objects.get(
            record_name='hostname.example.com',
            field_name='name',
            user=self.user,
        )
        self.assertEqual(history.old_value, '')
        self.assertEqual(history.new_value, 'hostname.exmaple.com')
        history = DNSHistory.objects.get(
            record_name='hostname.example.com',
            field_name='content',
            user=self.user,
        )
        self.assertEqual(history.old_value, '')
        self.assertEqual(history.new_value, '127.0.0.1')

    def test_record_modify(self):
        record = Record(
            name='hostname.example.com',
            type='A',
            content='127.0.0.1',
            domain=self.domain,
        )
        record.saving_user = self.user
        record.save()
        DNSHistory.objects.all().delete()
        record.content = '127.0.1.1'
        record.save()
        history = DNSHistory.objects.get(
            record_name='hostname.example.com',
            field_name='content',
            user=self.user,
        )
        self.assertEqual(history.old_value, '127.0.0.1')
        self.assertEqual(history.new_value, '127.0.1.1')

    @skip("Broken signals not being called")
    def test_record_delete(self):
        record = Record(
            name='hostname.example.com',
            type='A',
            content='127.0.0.1',
            domain=self.domain,
        )
        record.saving_user = self.user
        record.save()
        DNSHistory.objects.all().delete()
        record.delete()
        history = DNSHistory.objects.get(
            record_name='hostname.example.com',
            field_name='delete',
            user=self.user,
        )
        self.assertEqual(history.old_value, '127.0.0.1')
        self.assertEqual(history.new_value, '')
