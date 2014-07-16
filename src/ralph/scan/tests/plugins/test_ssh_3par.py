# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.scan.plugins.ssh_3par import _get_sys_info
from ralph.scan.tests.plugins.samples.ssh_3par import (
    SHOWSYS_1,
    SHOWSYS_2,
    SHOWSYS_3,
    SHOWSYS_WHITESPACES,
)


class Ssh3PARPluginTest(TestCase):
    def test_sys_info_1(self):
        result = _get_sys_info(SHOWSYS_1.split('\n'))
        self.assertEquals(result, ('3par-1-123', 'Server 12345', '5432109'))

    def test_sys_info_2(self):
        result = _get_sys_info(SHOWSYS_2.split('\n'))
        self.assertEquals(result, ('3par-2-123', 'Server 1234', '9876543'))

    def test_sys_info_3(self):
        result = _get_sys_info(SHOWSYS_3.split('\n'))
        self.assertEquals(result, ('3par-3-123', 'Server 1234', '12345'))

    def test_sys_info_whitespaces(self):
        result = _get_sys_info(SHOWSYS_WHITESPACES.split('\n'))
        self.assertEquals(result, ('3par-3-123', 'Server 1234', '12345'))
