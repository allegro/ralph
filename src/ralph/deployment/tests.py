# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from ralph.discovery.models import Device, DeviceType, DeviceModel
from ralph.business.models import Venture, VentureRole
from ralph.cmdb.models_ci import CIOwner, CIOwnership, CIOwnershipType, CI
from ralph.cmdb.importer import CIImporter
from ralph.deployment.models import Deployment, DeploymentStatus
from ralph.deployment.plugins.ticket import ticket
from ralph.deployment.models import get_business_owner, get_technical_owner
from django.contrib.contenttypes.models import ContentType



class DeploymentTest(TestCase):
    fixtures=['0_types.yaml', '1_attributes.yaml',
            '2_layers.yaml', '3_prefixes.yaml']

    def setUp(self):
        engine = settings.ISSUETRACKERS['default']['ENGINE']
        if engine != '':
            raise ImproperlyConfigured(
                '''Expected ISSUETRACKERS['default']['ENGINE']='' got: %r'''
                % engine)
        # usual stuff
        self.top_venture = Venture(name='top_venture')
        self.top_venture.save()
        self.child_venture = Venture(
            name='child_venture', parent=self.top_venture
        )
        self.child_venture.save()
        self.role = VentureRole(name='role', venture=self.child_venture)
        self.role.save()
        self.child_role = VentureRole(
            name='child_role',
            venture=self.child_venture,
            parent=self.role,
        )
        self.child_role.save()
        to = CIOwner(
            first_name='Bufallo', last_name='Kudłaczek',
        )
        to.save()
        bo = CIOwner(
            first_name='Bill', last_name='Bąbelek',
        )
        bo.save()
        ct = ContentType.objects.get_for_model(self.top_venture)
        CIImporter().import_all_ci([ct])
        CIOwnership(
            owner=to,
            ci=CI.get_by_content_object(self.child_venture),
            type=CIOwnershipType.technical.id
        ).save()
        CIOwnership(
            owner=bo,
            ci=CI.get_by_content_object(self.child_venture),
            type=CIOwnershipType.business.id
        ).save()
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
            model=dm
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


    def test_acceptance(self):
        # using issue null engine
        self.assertEqual(self.deployment.status, DeploymentStatus.open.id)
        self.deployment.create_issue()
        self.assertEqual(self.deployment.issue_key, '#123456')
        # status not changed, until plugin is run
        self.assertEqual(self.deployment.status, DeploymentStatus.open.id)
        # run ticket acceptance plugin
        ticket(self.deployment.id)
        # ticket already accepted
        self.deployment = Deployment.objects.get(id=self.deployment.id)
        self.assertEqual(
            self.deployment.status, DeploymentStatus.in_deployment.id
        )

    def test_owners(self):
        self.assertEqual(get_technical_owner(self.deployment.device),
                         'bufallo.kudlaczek')
        self.assertEqual(get_business_owner(self.deployment.device), 'bill.babelek')

    def add_model(self, name, device_type):
        dm = DeviceModel();
        dm.model_type = device_type,
        dm.name = name
        dm.save()
        return dm

