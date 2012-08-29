# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.business.models import Venture, VentureRole
from ralph.discovery.models_network import Network, NetworkTerminator, DataCenter

class TestModels(TestCase):
    def test_venture_path(self):
        a = Venture(name='A', symbol='a')
        a.save()
        b = Venture(name='B', symbol='b')
        b.save()

        self.assertEqual(a.path, 'a')
        self.assertEqual(b.path, 'b')

        b.parent = a
        b.save()

        self.assertEqual(a.path, 'a')
        self.assertEqual(b.path, 'a/b')

    def test_role_full_name(self):
        a = Venture(name='A', symbol='a')
        a.save()
        x = VentureRole(name='x', venture=a)
        x.save()
        y = VentureRole(name='y', venture=a, parent=x)
        y.save()

        self.assertEqual(y.full_name, 'x / y')
        
    def test_check_ip(self):
        terminator = NetworkTerminator(name='Test Terminator')
        terminator.save()

        data_center = DataCenter(name='Test date_center')
        data_center.save()
        
        network = Network(address='192.168.1.0/24',name='Test network', 
                          data_center=data_center)
        network.save()
        network.terminators = [terminator]
        network.save()
            
        main_venture = Venture(name='Main Venture')
        main_venture.save()
        main_venture.network = [network]
        main_venture.save()
        
        second_network = Network(address='172.16.0.0/28',name='Test secound_network', 
                          data_center=data_center)
        second_network.save()
        second_network.terminators = [terminator]
        second_network.save()
        
        child_venture = Venture(name='Child Venture', parent=main_venture)
        child_venture.save()
        child_venture.network = [second_network]
        child_venture.save()
        
        third_network = Network(address='66.6.6.0/29',name='Test third_network', 
                          data_center=data_center)
        third_network.save()
        third_network.terminators = [terminator]
        third_network.save()
        
        venture_role_main = VentureRole(name='Main Venture role', 
                                        venture=child_venture)
        venture_role_main.save()
        venture_role_main.network = [third_network]
        venture_role_main.save()
        
        fourth_network = Network(address='111.11.11.0/27',name='Test fourth_network', 
                          data_center=data_center)
        fourth_network.save()
        fourth_network.terminators = [terminator]
        fourth_network.save()
        
        venture_role_child = VentureRole(name='Child Venture role', 
                                         venture=child_venture, 
                                         parent=venture_role_main)
        venture_role_child.save()
        venture_role_child.network = [fourth_network]
        venture_role_child.save()

        self.assertEqual(venture_role_child.check_ip("192.168.1.15"), True)
        self.assertEqual(venture_role_child.check_ip("192.168.2.15"), None)

        self.assertEqual(venture_role_child.check_ip("172.16.0.10"), True)
        self.assertEqual(venture_role_child.check_ip("172.16.0.22"), None)
        
        self.assertEqual(venture_role_child.check_ip("66.6.6.5"), True)
        self.assertEqual(venture_role_child.check_ip("66.6.6.10"), None)
        
        self.assertEqual(venture_role_child.check_ip("111.11.11.1"), True)
        self.assertEqual(venture_role_child.check_ip("111.11.11.44"), None)