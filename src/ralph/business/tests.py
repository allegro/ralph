# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from django.conf import settings
from ralph.business.models import Venture, VentureRole

import pdb

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
        
    def test_get_iso_none(self):
        a = Venture(name='test1', symbol='test1')
        a.save()
        b = Venture(name='test1 parent', symbol='test1_parent', parent_id = a.id)
        b.save()
        c = Venture(name='test1 parent parent', symbol='test1_parent_parent', parent_id = b.id)
        c.save()

        self.assertEqual(a.get_iso_path(), settings.DEFAULT_ISO_PATH)        
        self.assertEqual(c.get_iso_path(), settings.DEFAULT_ISO_PATH)        

    def test_get_iso(self):
        iso = 'iso'
        
        a = Venture(name='test1', symbol='test1', iso_path = iso)
        a.save()
        b = Venture(name='test1 parent', symbol='test1_parent', parent_id = a.id)
        b.save()
        c = Venture(name='test1 parent parent', symbol='test1_parent_parent', parent_id = b.id)
        c.save()
                
        self.assertEqual(a.get_iso_path(), iso)
        self.assertEqual(b.get_iso_path(), iso)         
        self.assertEqual(c.get_iso_path(), iso)  

    def get_kickstart_path_none(self):
        a = Venture(name='test1', symbol='test1')
        a.save()
        b = Venture(name='test1 parent', symbol='test1_parent', parent_id = a.id)
        b.save()
        c = Venture(name='test1 parent parent', symbol='test1_parent_parent', parent_id = b.id)
        c.save()
                         
        self.assertIsNone(a.get_kickstart_path())     
        self.assertIsNone(c.get_kickstart_path())
       
    def test_get_kickstart(self):
        kick_path = '/simple/path'
        
        a = Venture(name='test1', symbol='test1', kickstart_path = kick_path)
        a.save()
        b = Venture(name='test1 parent', symbol='test1_parent', parent_id = a.id)
        b.save()
        c = Venture(name='test1 parent parent', symbol='test1_parent_parent', parent_id = b.id)
        c.save()
                
        self.assertEqual(a.get_kickstart_path(), kick_path)
        self.assertEqual(b.get_kickstart_path(), kick_path)    
        self.assertEqual(c.get_kickstart_path(), kick_path)        
#
#    def test_get_kickstart2(self):
#        # if kick == None
#        
#        a = Venture(name='test1', symbol='test1')
#        a.save()
#        b = Venture(name='test1 parent', symbol='test1_parent', parent_id = a.id)
#        b.save()
#        c = Venture(name='test1 parent parent', symbol='test1_parent_parent', parent_id = b.id)
#        c.save()
#                         
#        self.assertIsNone(a.get_kickstart_path())     
#        self.assertIsNone(c.get_kickstart_path())      
#
#
#    def test_get_iso_role(self):
#        # if iso == None
#        ven = Venture(name='test1', symbol='test1')
#        ven.save()
#
#        a = VentureRole(name='test1', venture_id = ven.id)
#        a.save()
#        b = VentureRole(name='test1 parent', parent_id = a.id, venture_id = ven.id)
#        b.save()
#        c = VentureRole(name='test1 parent parent', parent_id = b.id, venture_id = ven.id)
#        c.save()
#
#        self.assertEqual(a.get_iso_path_role(), settings.DEFAULT_ISO_PATH)
#        self.assertEqual(b.get_iso_path_role(), settings.DEFAULT_ISO_PATH)         
#        self.assertEqual(c.get_iso_path_role(), settings.DEFAULT_ISO_PATH)
#    
#    def test_get_iso_role2(self):
#        # if iso != None
#        iso = 'iso'
#        ven = Venture(name='test1', symbol='test1', iso_path = iso)
#        ven.save()
#        
#        a = VentureRole(name='test1', iso_path = iso, venture_id = ven.id)
#        a.save()
#        b = VentureRole(name='test1 parent', parent_id = a.id, venture_id = ven.id)
#        b.save()
#        c = VentureRole(name='test1 parent parent', parent_id = b.id, venture_id = ven.id)
#        c.save()
#                
#        self.assertEqual(a.get_iso_path_role(), iso)
#        self.assertEqual(b.get_iso_path_role(), iso)         
#        self.assertEqual(c.get_iso_path_role(), iso)
#
#    def test_get_kickstart_role(self):
#        # if kick == None
#        ven = Venture(name='test1', symbol='test1')
#        ven.save()
#        
#        a = VentureRole(name='test1', venture_id = ven.id)
#        a.save()
#        b = VentureRole(name='test1 parent', parent_id = a.id, venture_id = ven.id)
#        b.save()
#        c = VentureRole(name='test1 parent parent', parent_id = b.id, venture_id = ven.id)
#        c.save()
#                
#        self.assertIsNone(a.get_kickstart_path_role())  
#        self.assertIsNone(b.get_kickstart_path_role())  
#        self.assertIsNone(c.get_kickstart_path_role()) 
#
#    def test_get_kickstart_role2(self):
#        # if kick != None
#        kick = '/path/to/kickstart'
#        ven = Venture(name='test1', symbol='test1', kickstart_path = kick)
#        ven.save()
#        
#        a = VentureRole(name='test1', venture_id = ven.id)
#        a.save()
#        b = VentureRole(name='test1 parent', parent_id = a.id, venture_id = ven.id)
#        b.save()
#        c = VentureRole(name='test1 parent parent', parent_id = b.id, venture_id = ven.id)
#        c.save()
# 
#        self.assertEqual(a.get_kickstart_path_role(), kick)
#        self.assertEqual(b.get_kickstart_path_role(), kick)         
#        self.assertEqual(c.get_kickstart_path_role(), kick)
#    
#
