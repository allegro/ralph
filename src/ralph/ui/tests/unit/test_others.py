# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.tests.util import (
    DeviceFactory,
    LoadBalancerVirtualServerFactory,
)
from ralph.ui.views.common import _get_balancers


class TestAddresses(TestCase):

    def test_got_balancers_when_no_default_pool(self):
        lbvs = LoadBalancerVirtualServerFactory()
        self.assertIsNone(lbvs.default_pool)
        balancers = list(_get_balancers(lbvs.device))
        self.assertIsNone(balancers[0]['pool'])
