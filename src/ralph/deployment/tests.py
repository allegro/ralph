# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.models import Device, DeviceType, DeviceModel
from ralph.business.models import Venture, VentureRole
from ralph.deployment.models import Deployment


class DeploymentTest(TestCase):
    def setUp(self):
        self.top_venture = Venture(name='top_venture')
        self.top_venture.save()
        self.child_venture = Venture(
            name='child_venture',
            parent=self.top_venture,
        )
        self.child_venture.save()
        self.role = VentureRole(
            name='role',
            venture=self.child_venture,
        )
        self.role.save()
        self.child_role = VentureRole(
            name='child_role',
            venture=self.child_venture,
            parent=self.role,
        )
        self.child_role.save()
        dm = self.add_model('DC model sample', DeviceType.data_center.id)
        self.dc = Device.create(sn='sn1', model=dm)
        self.dc.name = 'dc'
        self.dc.save()
        dm = self.add_model('Rack model sample', DeviceType.rack_server.id)
        self.rack = Device.create(
            venture=self.child_venture,
            sn='sn2',
            model=dm,
        )
        self.rack.parent = self.dc
        self.rack.name = 'rack'
        self.rack.save()
        dm = self.add_model('Blade model sample', DeviceType.blade_server.id)
        self.blade = Device.create(
            venture=self.child_venture,
            venturerole=self.child_role,
            sn='sn3',
            model=dm,
        )
        self.blade.name = 'blade'
        self.blade.parent = self.rack
        self.blade.save()
        self.deployment = Deployment()
        self.deployment.hostname = 'test_host2'
        self.deployment.device = self.blade
        self.deployment.mac = '10:9a:df:6f:af:01'
        self.deployment.ip = '192.168.1.1'
        self.deployment.hostname = 'test'
        self.deployment.save()

    def add_model(self, name, device_type):
        dm = DeviceModel()
        dm.model_type = device_type,
        dm.name = name
        dm.save()
        return dm

