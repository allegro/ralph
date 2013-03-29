# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import skipIf

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.business.models import (
    Venture,
    VentureRole,
    BusinessLine,
    Service,
)
from ralph.cmdb.importer import CIImporter
from ralph.cmdb.models import (
    CI,
    CIRelation,
    CI_RELATION_TYPES,
)
from ralph.discovery.models import (
    Device,
    DeviceType,
    DeviceModel,
    DataCenter,
    Network,
)


CURRENT_DIR = settings.CURRENT_DIR


class CIImporterTest(TestCase):
    """Test creating CI's and relations between them from base ralph data types."""
    def setUp(self):
        self.top_venture = Venture(name='top_venture')
        self.top_venture.save()

        self.child_venture = Venture(
            name='child_venture', parent=self.top_venture)
        self.child_venture.save()

        self.role = VentureRole(name='role', venture=self.child_venture)
        self.role.save()
        self.child_role = VentureRole(
            name='child_role',
            venture=self.child_venture,
            parent=self.role,
        )
        self.child_role.save()
        dm = self.add_model('DC model sample', DeviceType.data_center)
        self.dc = Device.create(sn='sn1', model=dm)
        self.dc.name = 'dc'
        self.dc.save()
        dm = self.add_model('Rack model sample', DeviceType.rack_server)
        self.rack = Device.create(
            venture=self.child_venture,
            sn='sn2',
            model=dm,
        )
        self.rack.parent = self.dc
        self.rack.name = 'rack'
        self.rack.save()
        dm = self.add_model('Blade model sample', DeviceType.blade_server)
        self.blade = Device.create(
            venture=self.child_venture,
            sn='sn3',
            model=dm,
        )
        self.blade.name = 'blade'
        self.blade.venture_role = self.child_role
        self.blade.parent = self.rack
        self.blade.save()

    def add_model(self, name, device_type):
        dm = DeviceModel()
        dm.model_type = device_type
        dm.name = name
        dm.save()
        return dm

    def test_import_devices(self):
        """
        Test importing:
        - prefixes
        - parenthesis
        - layers

        Structure:

        top_venture
            <--child_venture
                <---role
                    <---child_role
                        <----dc
                            <----rack
                                <----blade
        """
        # ventures and roles
        objs = [self.top_venture, self.child_venture, self.role,
                self.child_role]
        for o in objs:
            ct = ContentType.objects.get_for_model(o)
            CIImporter().import_all_ci([ct], asset_id=o.id)
        for o in objs:
            ct = ContentType.objects.get_for_model(o)
            CIImporter().import_relations(ct, asset_id=o.id)

        # devices
        objs = [self.dc, self.rack, self.blade]
        # create ci
        for o in objs:
            ct = ContentType.objects.get_for_model(o)
            CIImporter().import_all_ci([ct], asset_id=o.id)
            # create relations
        for o in objs:
            ct = ContentType.objects.get_for_model(o)
            CIImporter().import_relations(ct, asset_id=o.id)

        # All ci should be in Hardware layer
        ci_dc = CI.objects.get(name='dc')
        ci_rack = CI.objects.get(name='rack')
        ci_blade = CI.objects.get(name='blade')
        ci_venture = CI.objects.get(name='child_venture')
        ci_role = CI.objects.get(name='child_role')

        self.assertEqual(ci_dc.layers.select_related()[0].name, 'Hardware')
        self.assertEqual(ci_rack.layers.select_related()[0].name, 'Hardware')
        self.assertEqual(ci_blade.layers.select_related()[0].name, 'Hardware')
        # Reimport of relations should not raise Exception,
        # and should not change relations count
        cis = []
        for o in objs:
            ct = ContentType.objects.get_for_model(o)
            cis.extend(
                CIImporter().import_all_ci([ct], asset_id=o.id),
            )
            # Rack should be inside DC
        try:
            CIRelation.objects.get(
                parent=ci_dc, child=ci_rack,
                type=CI_RELATION_TYPES.CONTAINS.id)
        except CIRelation.DoesNotExist:
            self.fail('Cant find relation %s %s %s' % (ci_dc, ci_rack))
            # Blade should be inside Rack
        CIRelation.objects.get(
            parent=ci_rack,
            child=ci_blade,
            type=CI_RELATION_TYPES.CONTAINS.id,
        )

        # every device in composition chain should have relation
        # to Venture and Role as well.
        # test relations -
        # dc - no role no venture
        # rack - venture, no role
        # blade - venture and role
        venture_rels = CIRelation.objects.filter(
            child__in=[ci_dc, ci_rack, ci_blade],
            parent=ci_venture,
            type=CI_RELATION_TYPES.CONTAINS.id,
        )
        # dc is *not* bound to venture
        self.assertEqual(
            set([(rel.parent.name, rel.child.name, rel.type) for rel in venture_rels]),
            set([(u'child_venture', u'rack', 1),
                 (u'child_venture', u'blade', 1)])
        )
        role_rels = CIRelation.objects.filter(
            child__in=[ci_dc, ci_rack, ci_blade],
            parent=ci_role,
            type=CI_RELATION_TYPES.HASROLE.id,
        )
        # only bottom level device has role, so one relation is made
        self.assertEqual(
            set([(rel.parent.name, rel.child.name, rel.type) for rel in role_rels]),
            set([(u'child_role', u'blade', 3)]),
        )
        from ralph.cmdb.graphs import ImpactCalculator
        # summarize relations.
        self.assertEqual(CIRelation.objects.count(), 9)
        # calculate impact/spanning tree for CI structure
        root_ci = CI.objects.get(name='rack')
        calc = ImpactCalculator(root_ci)
        self.assertEqual(
            calc.find_affected_nodes(root_ci.id),
            ({2: 6, 5: 6, 6: None, 7: 6}, [6, 7, 2, 5]),
        )


class AddOrUpdateCITest(TestCase):
    def setUp(self):
        # create Venture and CI
        self.venture = Venture.objects.create(name='TestVenture')

        # create VentureRole and CI
        v = Venture.objects.create(name='SomeAssignedVenture')
        self.venture_role = VentureRole.objects.create(
            name='TestVentureRole',
            venture=v,
        )

        # create DataCenter and CI
        self.data_center = DataCenter.objects.create(name='DC123')

        # create Network and CI
        dc = DataCenter.objects.create(name='SomeDC')
        self.network = Network.objects.create(
            name='TestNetwork',
            address='192.168.56.1',
            data_center=dc,
        )

        # create Device and CI
        device_model = DeviceModel.objects.create(
            name='SomeDeviceModel', type=DeviceType.rack_server.id,
        )
        self.device = Device.create(
            name='TestDevice', sn='sn123', model=device_model,
        )

        # create Service and CI
        bl = BusinessLine.objects.create(name='Some Business Line')
        self.service = Service.objects.create(
            name='someservice.com',
            external_key='abc123',
            business_line=bl.name,
        )

        # create BusinessLIne and CI
        self.business_line = BusinessLine.objects.create(
            name='TestBusinessLine',
        )

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_add_ci(self):
        assets = [
            self.venture, self.venture_role, self.data_center, self.network,
            self.device, self.service, self.business_line,
        ]
        for asset in assets:
            ci = CI.get_by_content_object(asset)
        self.assertIsNotNone(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_update_ci(self):
        self.venture.name = 'New Venture name'
        self.venture.save()
        venture = Venture.objects.get(id=self.venture.id)
        ci = CI.get_by_content_object(venture)
        self.assertEqual(venture.name, ci.name)
        self.assertEqual(ci.name, 'New Venture name')

        self.device.barcode = '1111-1111-2222-2222'
        self.device.save()
        device = Device.objects.get(id=self.device.id)
        ci = CI.get_by_content_object(device)
        self.assertEqual(device.barcode, ci.barcode)
        self.assertEqual(ci.barcode, '1111-1111-2222-2222')


class AutoCIRemoveTest(TestCase):
    def setUp(self):
        # create Venture and CI
        self.venture = Venture.objects.create(name='TestVenture')

        # create VentureRole and CI
        v = Venture.objects.create(name='SomeAssignedVenture')
        self.venture_role = VentureRole.objects.create(
            name='TestVentureRole', venture=v,
        )

        # create DataCenter and CI
        self.data_center = DataCenter.objects.create(name='DC123')

        # create Network and CI
        dc = DataCenter.objects.create(name='SomeDC')
        self.network = Network.objects.create(
            name='TestNetwork',
            address='192.168.56.1',
            data_center=dc,
        )

        # create Device and CI
        device_model = DeviceModel.objects.create(
            name='SomeDeviceModel',
            type=DeviceType.rack_server,
        )
        self.device = Device.create(
            name='TestDevice',
            sn='sn123',
            model=device_model,
        )

        # create Service and CI
        bl = BusinessLine.objects.create(name='Some Business Line')
        self.service = Service.objects.create(
            name='someservice.com',
            external_key='abc123',
            business_line=bl.name,
        )

        # create BusinessLIne and CI
        self.business_line = BusinessLine.objects.create(
            name='TestBusinessLine',
        )

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_venture(self):
        ci = CI.get_by_content_object(self.venture)
        self.assertIsNotNone(ci)
        self.venture.delete()

        ci = CI.get_by_content_object(self.venture)
        self.assertFalse(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_venture_role(self):
        ci = CI.get_by_content_object(self.venture_role)
        self.assertIsNotNone(ci)

        self.venture_role.delete()

        ci = CI.get_by_content_object(self.venture_role)
        self.assertFalse(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_datacenter(self):
        ci = CI.get_by_content_object(self.data_center)
        self.assertIsNotNone(ci)

        self.data_center.delete()

        ci = CI.get_by_content_object(self.data_center)
        self.assertFalse(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_network(self):
        ci = CI.get_by_content_object(self.network)
        self.assertIsNotNone(ci)

        self.network.delete()

        ci = CI.get_by_content_object(self.network)
        self.assertFalse(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_device(self):
        ci = CI.get_by_content_object(self.device)
        self.assertIsNotNone(ci)
        self.device.delete()

        ci = CI.get_by_content_object(self.device)
        self.assertFalse(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_service(self):
        ci = CI.get_by_content_object(self.service)
        self.assertIsNotNone(ci)

        self.service.delete()

        ci = CI.get_by_content_object(self.service)
        self.assertFalse(ci)

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_remove_businessline(self):
        ci = CI.get_by_content_object(self.business_line)
        self.assertIsNotNone(ci)

        self.business_line.delete()

        ci = CI.get_by_content_object(self.business_line)
        self.assertFalse(ci)
