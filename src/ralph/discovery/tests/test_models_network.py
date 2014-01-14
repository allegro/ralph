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

    def test_get_netmask(self):
        net1 = Network(
            name="test1",
            data_center=self.dc,
            address="192.168.0.1/16",
        )
        net1.save()
        net2 = Network(
            name="test2",
            data_center=self.dc,
            address="192.168.0.1/17",
        )
        self.assertEquals(net1.get_netmask(), 16)
        self.assertEquals(net2.get_netmask(), 17)

    def test_get_network_tree(self):
        net1 = Network(
            name="test1",
            data_center=self.dc,
            address="192.168.0.1/16",
        )
        net1.save()
        net2 = Network(
            name="test2",
            data_center=self.dc,
            address="192.168.0.1/17",
        )
        net2.save()
        net3 = Network(
            name="test3",
            data_center=self.dc,
            address="192.168.128.1/17",
        )
        net3.save()
        net4 = Network(
            name="test4",
            data_center=self.dc,
            address="192.168.133.1/24",
        )
        net4.save()
        net5 = Network(
            name="test5",
            data_center=self.dc,
            address="192.169.133.1/24",
        )
        net5.save()

        res = net1.get_subnetworks()
        correct = [net2, net3]
        self.assertEquals(res, correct)

        res = net3.get_subnetworks()
        correct = [net4]
        self.assertEquals(res, correct)

    def test_get_next_free_subnet(self):
        net1 = Network(
            name="test1",
            data_center=self.dc,
            address="192.168.0.1/16",
        )
        net1.save()
        net2 = Network(
            name="test2",
            data_center=self.dc,
            address="192.168.0.1/17",
        )
        net2.save()
        res = net1.get_next_free_subnet()
        correct = "192.168.128.1/17"
        self.assertEquals(res, correct)
