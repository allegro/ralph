# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import Network, DataCenter


class ModelsNetworkTest(TestCase):
    def setUp(self):
        self.dc = DataCenter(name="test_dc")
        self.dc.save()
        self.net1 = Network(
            name="test1",
            data_center=self.dc,
            address="192.168.0.1/16",
        )
        self.net1.save()
        self.net2 = Network(
            name="test2",
            data_center=self.dc,
            address="192.168.0.1/17",
        )
        self.net2.save()
        self.net3 = Network(
            name="test3",
            data_center=self.dc,
            address="192.168.128.1/17",
        )
        self.net3.save()
        self.net4 = Network(
            name="test4",
            data_center=self.dc,
            address="192.168.133.1/24",
        )
        self.net4.save()
        self.net5 = Network(
            name="test5",
            data_center=self.dc,
            address="192.169.133.1/24",
        )
        self.net5.save()

    def test_get_netmask(self):
        self.assertEquals(self.net1.get_netmask(), 16)
        self.assertEquals(self.net2.get_netmask(), 17)

    def test_get_network_tree(self):
        res = self.net1.get_subnetworks()
        correct = [self.net2, self.net3]
        self.assertEquals(res, correct)

        res = self.net3.get_subnetworks()
        correct = [self.net4]
        self.assertEquals(res, correct)

    def test_prepare_network_tree(self):
        res = Network.prepare_network_tree()
        correct = [
            {
                'network': self.net1,
                'subnetworks': [
                    {
                        'network': self.net2,
                        'subnetworks': [],
                    },
                    {
                        'network': self.net3,
                        'subnetworks': [
                            {
                                'network': self.net4,
                                'subnetworks': [],
                            }
                        ]
                    },
                ]
            },
            {
                'network': self.net5,
                'subnetworks': [],
            }
        ]
        self.assertEqual(res, correct)
