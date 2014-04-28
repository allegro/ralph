# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.business.models import Venture, VentureRole
from ralph.discovery.models_network import Network, NetworkTerminator, DataCenter
from ralph.deployment.models import Preboot


class ModelsTest(TestCase):

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

    def test_get_preboot_none(self):
        a = Venture(name='test1', symbol='test1')
        a.save()
        b = Venture(name='test1 parent', symbol='test1_parent', parent_id=a.id)
        b.save()
        c = Venture(
            name='test1 parent parent', symbol='test1_parent_parent', parent_id=b.id)
        c.save()

        self.assertEqual(a.get_preboot(), None)
        self.assertEqual(c.get_preboot(), None)

    def test_get_preboot(self):
        preboot = Preboot(name='test preboot')
        preboot.save()

        a = Venture(name='test1', symbol='test1', preboot=preboot)
        a.save()
        b = Venture(name='test1 parent', symbol='test1_parent', parent_id=a.id)
        b.save()
        c = Venture(
            name='test1 parent parent', symbol='test1_parent_parent', parent_id=b.id)
        c.save()

        self.assertEqual(a.get_preboot(), preboot)
        self.assertEqual(b.get_preboot(), preboot)
        self.assertEqual(c.get_preboot(), preboot)

    def test_get_preboot_role_none(self):
        ven = Venture(name='test1', symbol='test1')
        ven.save()

        a = VentureRole(name='test1', venture_id=ven.id)
        a.save()
        b = VentureRole(name='test1 parent', parent_id=a.id, venture_id=ven.id)
        b.save()
        c = VentureRole(
            name='test1 parent parent', parent_id=b.id, venture_id=ven.id)
        c.save()

        self.assertEqual(a.get_preboot(), None)
        self.assertEqual(b.get_preboot(), None)
        self.assertEqual(c.get_preboot(), None)

    def test_get_preboot_role(self):
        preboot = Preboot(name='test preboot')
        preboot.save()
        ven = Venture(name='test1', symbol='test1', preboot=preboot)
        ven.save()

        a = VentureRole(name='test1', preboot=preboot, venture_id=ven.id)
        a.save()
        b = VentureRole(name='test1 parent', parent_id=a.id, venture_id=ven.id)
        b.save()
        c = VentureRole(
            name='test1 parent parent', parent_id=b.id, venture_id=ven.id)
        c.save()
        self.assertEqual(a.get_preboot(), preboot)
        self.assertEqual(b.get_preboot(), preboot)
        self.assertEqual(c.get_preboot(), preboot)

    def test_get_data_center(self):
        data_center = DataCenter(name='Test DateCenter')
        data_center.save()
        ven = Venture(name='test', symbol='test', data_center=data_center)
        ven.save()

        a = Venture(name='test1', symbol='test1', parent=ven)
        a.save()
        b = Venture(name='test2', symbol='test1 parent', parent=a)
        b.save()
        c = Venture(name='test3', symbol='test1 parent parent', parent=b)
        c.save()
        self.assertEqual(a.get_data_center(), data_center)
        self.assertEqual(b.get_data_center(), data_center)
        self.assertEqual(c.get_data_center(), data_center)
