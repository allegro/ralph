# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import mock


from django.db.utils import IntegrityError
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from lxml import objectify
from mock import patch
from os.path import join as djoin

from ralph.discovery.models import (Device, DeviceType, DeviceModel,
                                    DataCenter, Network)
from ralph.business.models import Venture, VentureRole, Service, BusinessLine
from ralph.cmdb.importer import CIImporter
from ralph.cmdb.models import (CI, CILayer, CIRelation, CI_RELATION_TYPES,
                               CIChange, CI_TYPES, CIChangePuppet, CIChangeGit,
                               CI_CHANGE_TYPES, CIType)
from ralph.cmdb.integration.puppet import PuppetAgentsImporter
from ralph.cmdb.models import PuppetLog
from ralph.cmdb.integration.puppet import PuppetGitImporter as pgi
from ralph.cmdb.integration.issuetracker_plugins.jira import JiraRSS
from ralph.deployment.models import DeploymentPoll


CURRENT_DIR = settings.CURRENT_DIR


class MockFisheye(object):
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return mock.Mock()

    def get_changes(self, *args, **kwargs):
        xml = open(
            djoin(CURRENT_DIR, 'cmdb/tests/samples/fisheye_changesets.xml')
        ).read()
        return objectify.fromstring(xml)

    def get_details(self, *args, **kwargs):
        xml = open(
            djoin(CURRENT_DIR + 'cmdb/tests/samples/fisheye_details.xml')
        ).read()
        return objectify.fromstring(xml)


class CIImporterTest(TestCase):
    fixtures = [
        '0_types.yaml',
        '1_attributes.yaml',
        '2_layers.yaml',
        '3_prefixes.yaml'
    ]

    def setUp(self):
        self.top_venture = Venture(name='top_venture')
        self.top_venture.save()

        self.child_venture = Venture(
            name='child_venture', parent=self.top_venture)
        self.child_venture.save()

        self.role = VentureRole(name='role', venture=self.child_venture)
        self.role.save()
        self.child_role = VentureRole(
            name='child_role', venture=self.child_venture, parent=self.role,
        )
        self.child_role.save()
        dm = self.add_model('DC model sample', DeviceType.data_center.id)
        self.dc = Device.create(
            sn='sn1', model=dm
        )
        self.dc.name = 'dc'
        self.dc.save()
        dm = self.add_model('Rack model sample', DeviceType.rack_server.id)
        self.rack = Device.create(
            venture=self.child_venture,
            sn='sn2',
            model=dm
        )
        self.rack.parent = self.dc
        self.rack.name = 'rack'
        self.rack.save()
        dm = self.add_model('Blade model sample', DeviceType.blade_server.id)
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

    def test_puppet_parser(self):
        hostci = CI(name='s11401.dc2', uid='mm-1')
        hostci.type_id = CI_TYPES.DEVICE.id
        hostci.save()
        p = PuppetAgentsImporter()
        yaml = open(
            djoin(CURRENT_DIR, 'cmdb/tests/samples/canonical.yaml')
        ).read()
        p.import_contents(yaml)
        yaml = open(
            djoin(CURRENT_DIR, 'cmdb/tests/samples/canonical_unchanged.yaml')
        ).read()
        p.import_contents(yaml)
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_AGENT.id)
        logs = PuppetLog.objects.filter(
            cichange__host='s11401.dc2').order_by('id')
        self.assertEqual(chg.content_object.host, u's11401.dc2')
        self.assertEqual(chg.content_object.kind, u'apply')
        self.assertEqual(chg.ci, hostci)
        self.assertEqual(chg.type, 2)
        # check parsed logs
        self.assertEqual(len(logs), 16)
        time_iso = logs[0].time.isoformat().split('.')[0]
        self.assertEqual(time_iso, datetime.datetime(
            2010, 12, 31, 0, 56, 37).isoformat())
        # should not import puppet report which has 'unchanged' status
        self.assertEqual(
            CIChangePuppet.objects.filter(status='unchanged').count(), 0)

    def test_fisheye(self):
        """
        Create Venture/Role and import as CI/CIRelations.
        Now import fisheye xml from samples/* files and compare
        if changes are properly saved into the database,
        and reconcilated.
        """
        x = Venture(symbol='test_venture')
        x.save()
        y = VentureRole(name='test_role', venture=x)
        y.save()
        allegro_ci = CI(name='Allegro', type_id=CI_TYPES.VENTURE.id)
        allegro_ci.save()
        ct = ContentType.objects.get_for_model(x)
        test_venture, = CIImporter().import_all_ci([ct], asset_id=x.id)
        ct = ContentType.objects.get_for_model(y)
        test_role, = CIImporter().import_all_ci([ct], asset_id=y.id)
        CIImporter().import_relations(
            ContentType.objects.get_for_model(y), asset_id=y.id)
        with mock.patch(
                'ralph.cmdb.integration.lib.fisheye.Fisheye') as Fisheye:
            Fisheye.side_effect = MockFisheye
            x = pgi(fisheye_class=Fisheye)
            x.import_git()
        self.assertEqual(CIChangeGit.objects.filter(
            author__contains='johny.test@test.pl',
            #file_paths__contains='/test_venture'
        ).count(), 2)
        self.assertEqual(CIChange.objects.filter(
            ci=test_role,
            type=CI_CHANGE_TYPES.CONF_GIT.id,
        ).count(), 2)

        #todo
        # what if modified both core and venture?

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
                        <---- dc
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
        ci_role = CI.objects.get(name='dc')
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
                CIImporter().import_all_ci([ct], asset_id=o.id))
            # Rack should be inside DC
        try:
            CIRelation.objects.get(
                parent=ci_dc, child=ci_rack,
                type=CI_RELATION_TYPES.CONTAINS.id)
        except CIRelation.DoesNotExist:
            self.fail('Cant find relation %s %s %s' % (ci_dc, ci_rack))
            # Blade should be inside Rack
        CIRelation.objects.get(
            parent=ci_rack, child=ci_blade, type=CI_RELATION_TYPES.CONTAINS.id)

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
            set([(x.parent.name, x.child.name, x.type) for x in venture_rels]),
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
            set([(x.parent.name, x.child.name, x.type) for x in role_rels]),
            set([(u'child_role', u'blade', 3)]),
        )
        # summarize relations - 9
        self.assertEqual(len(CIRelation.objects.all()), 9)


class AutoCIRemoveTest(TestCase):
    fixtures = [
        '0_types.yaml',
        '1_attributes.yaml',
        '2_layers.yaml',
        '3_prefixes.yaml'
    ]

    def setUp(self):
        # create Venture and CI
        self.venture = Venture.objects.create(name='TestVenture')
        uid = CI.get_uid_by_content_object(self.venture)
        self.venture_ci_id = CI.objects.create(
            name='TestVentureCI', uid=uid, type_id=4).pk

        # create VentureRole and CI
        v = Venture.objects.create(name='SomeAssignedVenture')
        self.venture_role = VentureRole.objects.create(name='TestVentureRole',
                                                       venture=v)
        uid = CI.get_uid_by_content_object(self.venture_role)
        self.venture_role_ci_id = CI.objects.create(
            name='TestVentureRoleCI', uid=uid, type_id=5).pk

        # create DataCenter and CI
        self.data_center = DataCenter.objects.create(name='DC123')
        uid = CI.get_uid_by_content_object(self.data_center)
        self.data_center_ci_id = CI.objects.create(
            name='TestDataCenterCI', uid=uid, type_id=9).pk

        # create Network and CI
        dc = DataCenter.objects.create(name='SomeDC')
        self.network = Network.objects.create(name='TestNetwork',
                                              address='192.168.56.1',
                                              data_center=dc)
        uid = CI.get_uid_by_content_object(self.network)
        self.network_ci_id = CI.objects.create(
            name='TestNetworkCI', uid=uid, type_id=8).pk

        # create Device and CI
        device_model = DeviceModel.objects.create(
            name='SomeDeviceModel', type=DeviceType.rack_server.id)
        self.device = Device.create(name='TestDevice', sn='sn123',
                                    model=device_model)
        uid = CI.get_uid_by_content_object(self.device)
        self.device_ci_id = CI.objects.create(
            name='TestDeviceCI', uid=uid, type_id=2).pk

        # create Service and CI
        bl = BusinessLine.objects.create(name='Some Business Line')
        self.service = Service.objects.create(name='someservice.com',
                                              external_key='abc123',
                                              business_line=bl)
        uid = CI.get_uid_by_content_object(self.service)
        self.service_ci_id = CI.objects.create(
            name='TestServiceCI', uid=uid, type_id=7).pk

        # create BusinessLIne and CI
        self.business_line = BusinessLine.objects.create(
            name='TestBusinessLine')
        uid = CI.get_uid_by_content_object(self.business_line)
        self.business_line_ci_id = CI.objects.create(
            name='TestBusinessLineCI', uid=uid, type_id=6).pk

    def test_remove_venture(self):
        self.venture.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.venture_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)

    def test_remove_venture_role(self):
        self.venture_role.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.venture_role_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)

    def test_remove_datacenter(self):
        self.data_center.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.data_center_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)

    def test_remove_network(self):
        self.network.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.network_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)

    def test_remove_device(self):
        self.device.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.device_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)

    def test_remove_service(self):
        self.service.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.service_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)

    def test_remove_businessline(self):
        self.business_line.delete()
        ci = None
        try:
            ci = CI.objects.get(pk=self.business_line_ci_id)
        except CI.DoesNotExist:
            pass
        self.assertEquals(ci, None)


class JiraRssTest(TestCase):
    def setUp(self):
        settings.ISSUETRACKERS['JIRA'] = {'ENGINE': 'JIRA', 'USER': '',
                                          'PASSWORD': '', 'URL': '',
                                          'CMDB_PROJECT': ''}

    def tearDown(self):
        del settings.ISSUETRACKERS['JIRA']

    def get_datetime(self, data, format='%d-%m-%Y %H:%M'):
        return datetime.datetime.strptime(data, format)

    def test_get_new_issues(self):
        dp1_1 = DeploymentPoll(
            key='RALPH-341',
            date=datetime.datetime.strptime('1-1-2012 1:10', '%d-%m-%Y %H:%M')
        )
        dp1_1.save()
        dp1_2 = DeploymentPoll(
            key='RALPH-341',
            date=datetime.datetime.strptime('1-1-2012 1:20', '%d-%m-%Y %H:%M'))
        dp1_2.save()
        dp2_1 = DeploymentPoll(
            key='RALPH-342',
            date=datetime.datetime.strptime('2-2-2012 2:10', '%d-%m-%Y %H:%M'),
            checked=False)
        dp2_1.save()
        dp2_2 = DeploymentPoll(
            key='RALPH-342',
            date=datetime.datetime.strptime('2-2-2012 2:20', '%d-%m-%Y %H:%M'),
            checked=False)
        dp2_2.save()
        dp3_1 = DeploymentPoll(
            key='RALPH-343',
            date=datetime.datetime.strptime('3-3-2012 3:10', '%d-%m-%Y %H:%M')
        )
        dp3_1.save()
        dp3_2 = DeploymentPoll(
            key='RALPH-343',
            date=datetime.datetime.strptime('3-3-2012 3:20', '%d-%m-%Y %H:%M'))
        dp3_2.save()
        dp4_1 = DeploymentPoll(
            key='RALPH-344',
            date=datetime.datetime.strptime('4-4-2012 5:10', '%d-%m-%Y %H:%M'))
        dp4_1.save()
        x = JiraRSS(tracker_name='JIRA')
        rss = open(
            djoin(CURRENT_DIR, 'cmdb/tests/samples/jira_rss.xml')
        ).read()
        x.rss_url = rss
        self.assertEquals(
            sorted(x.get_new_issues()), [
                'RALPH-341', 'RALPH-342', 'RALPH-343', 'RALPH-344']
        )

_PATCHED_OP_TEMPLATE = 'test'
_PATCHED_OP_START_DATE = '2012-01-02'
_PATCHED_TICKETS_ENABLE = True
_PATCHED_USE_CELERY = False
_PATCHED_TICKETS_ENABLE_NO = False


class OPRegisterTest(TestCase):
    """ OP Changes such as git change, attribute change, is immiediatelly sent
    to issue tracker as CHANGE ticket for logging purporses. Check this
    workflow here
    """

    @patch('ralph.cmdb.models_signals.OP_TEMPLATE', _PATCHED_OP_TEMPLATE)
    @patch('ralph.cmdb.models_signals.OP_START_DATE', _PATCHED_OP_START_DATE)
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE',
           _PATCHED_TICKETS_ENABLE)
    @patch('ralph.cmdb.models_common.USE_CELERY', _PATCHED_USE_CELERY)
    def test_create_issues(self):
        # if change is registered after date of start, ticket is registered
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=2)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '#123456')
        self.assertEqual(chg.get_registration_type_display(), 'Change')
        CIChange.objects.all().delete()

        #removing cichange remove cichangegit child too.
        self.assertEqual(CIChangeGit.objects.count(), 0)

        # if change is registered before date of start, ticket is not
        # registered
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=1)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '')
        self.assertEqual(chg.get_registration_type_display(), 'Not registered')

    @patch('ralph.cmdb.models_signals.OP_TEMPLATE', _PATCHED_OP_TEMPLATE)
    @patch('ralph.cmdb.models_signals.OP_START_DATE', _PATCHED_OP_START_DATE)
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE',
           _PATCHED_TICKETS_ENABLE_NO)
    @patch('ralph.cmdb.models_common.USE_CELERY', _PATCHED_USE_CELERY)
    def test_dont_create_issues(self):
        # The date is ok, but tickets enabled is set to no.
        # Dont register ticket.
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=2)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        # yeah, ticket is not registered, because disabled in config.
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '')
        self.assertEqual(chg.get_registration_type_display(), 'Not registered')

DEVICE_NAME = 'SimpleDevice'
DEVICE_IP = '10.0.0.1'
DEVICE_REMARKS = 'Very important device'
DEVICE_VENTURE = 'SimpleVenture'
DEVICE_VENTURE_SYMBOL = 'simple_venture'
VENTURE_ROLE = 'VentureRole'
DEVICE_POSITION = '12'
DEVICE_RACK = '13'
DEVICE_BARCODE = 'bc_dev'
DEVICE_SN = '0000000001'
DEVICE_MAC = '00:00:00:00:00:00'
DATACENTER = 'dc1'


class CIFormsTest(TestCase):
    def setUp(self):
        login = 'ralph'
        password = 'ralph'
        user = User.objects.create_user(login, 'ralph@ralph.local', password)
        self.user = user
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client = Client()
        self.client.login(username=login, password=password)

        venture = Venture(name=DEVICE_VENTURE, symbol=DEVICE_VENTURE_SYMBOL)
        venture.save()
        self.venture = venture
        venture_role = VentureRole(name=VENTURE_ROLE, venture=self.venture)
        venture_role.save()
        self.venture_role = venture_role
        self.device = Device.create(
            sn=DEVICE_SN,
            barcode=DEVICE_BARCODE,
            remarks=DEVICE_REMARKS,
            model_name='xxxx',
            model_type=DeviceType.unknown,
            venture=self.venture,
            venture_role=self.venture_role,
            rack=DEVICE_RACK,
            position=DEVICE_POSITION,
            dc=DATACENTER,
        )
        self.device.name = DEVICE_NAME
        self.device.save()

        self.layer = CILayer(name='layer1')
        self.layer.save()
        self.citype = CIType(name='xxx')
        self.citype.save()

    def add_ci(self, name='CI'):
        ci_add_url = '/cmdb/add/'
        attrs = {
            'base-layers': 1,
            'base-name': name,
            'base-state': 2,
            'base-status': 2,
            'base-type': 1
        }
        return self.client.post(ci_add_url, attrs)

    def add_ci_relation(self, parent_ci, child_ci, relation_type,
                        relation_kind):
        ci_relation_add_url = '/cmdb/relation/add/{}?{}={}'.format(
            parent_ci.id, relation_type, parent_ci.id
        )
        attrs = {
            'base-parent': parent_ci.id,
            'base-child': child_ci.id,
            'base-type': relation_kind.id,
        }
        return self.client.post(ci_relation_add_url, attrs)

    def test_add_two_ci_with_the_same_content_object(self):
        response = self.add_ci(name='CI1')
        self.assertEqual(response.status_code, 302)
        ci1 = CI.objects.get(name='CI1')
        ci1.content_object = self.device
        ci1.save()

        response = self.add_ci(name='CI2')
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(IntegrityError) as e:
            ci2 = CI.objects.get(name='CI2')
            ci2.content_object = self.device
            ci2.save()
        self.assertEqual('columns content_type_id, object_id are not unique',
                         e.exception.message)

    def test_two_ci_without_content_object(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI1')
        cis = CI.objects.filter(name='CI1')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        self.assertEqual(len(cis), 2)

    def test_add_ci_relation_rel_child(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        ci1 = CI.objects.get(name='CI1')
        ci2 = CI.objects.get(name='CI2')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_child',
            relation_kind=CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci1.id, child_id=ci2.id,
                                     type=CI_RELATION_TYPES.HASROLE)
        self.assertEqual(rel.type, CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_child',
            relation_kind=CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(
            parent_id=ci1.id,
            child_id=ci2.id,
            type=CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(rel.type, CI_RELATION_TYPES.CONTAINS)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_child',
            relation_kind=CI_RELATION_TYPES.REQUIRES)
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci1.id, child_id=ci2.id,
                                     type=CI_RELATION_TYPES.REQUIRES)
        self.assertEqual(rel.type, CI_RELATION_TYPES.REQUIRES)

    def test_add_ci_relation_rel_parent(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        ci1 = CI.objects.get(name='CI1')
        ci2 = CI.objects.get(name='CI2')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci1.id, child_id=ci2.id,
                                     type=CI_RELATION_TYPES.HASROLE)
        self.assertEqual(rel.type, CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(
            parent_id=ci1.id,
            child_id=ci2.id,
            type=CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(rel.type, CI_RELATION_TYPES.CONTAINS)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.REQUIRES)
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci1.id, child_id=ci2.id,
                                     type=CI_RELATION_TYPES.REQUIRES)
        self.assertEqual(rel.type, CI_RELATION_TYPES.REQUIRES)

    def test_add_ci_relation_with_himself(self):
        response_ci = self.add_ci(name='CI')
        self.assertEqual(response_ci.status_code, 302)
        ci = CI.objects.get(name='CI')

        response_r = self.add_ci_relation(
            parent_ci=ci,
            child_ci=ci,
            relation_type='rel_child',
            relation_kind=CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.context_data['form'].errors['__all__'][0],
                         'CI can not have relation with himself')

    def test_ci_cycle_parent_child(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)

        ci1 = CI.objects.get(name='CI1')
        ci2 = CI.objects.get(name='CI2')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(response_r.status_code, 302)
        response_r = self.add_ci_relation(
            parent_ci=ci2,
            child_ci=ci1,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(response_r.status_code, 302)

    def test_ci_relations_cycle(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        response_ci3 = self.add_ci(name='CI3')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        self.assertEqual(response_ci3.status_code, 302)
        ci1 = CI.objects.get(name='CI1')
        ci2 = CI.objects.get(name='CI2')
        ci3 = CI.objects.get(name='CI3')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci1.id, child_id=ci2.id,
                                     type=CI_RELATION_TYPES.HASROLE)
        self.assertEqual(rel.type, CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci2,
            child_ci=ci3,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci2.id, child_id=ci3.id,
                                     type=CI_RELATION_TYPES.HASROLE)
        self.assertEqual(rel.type, CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci3,
            child_ci=ci1,
            relation_type='rel_parent',
            relation_kind=CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.status_code, 302)
        rel = CIRelation.objects.get(parent_id=ci3.id, child_id=ci1.id,
                                     type=CI_RELATION_TYPES.HASROLE)
        self.assertEqual(rel.type, CI_RELATION_TYPES.HASROLE)

        cycle = CI.get_cycle()
        self.assertEqual(cycle, [1, 2, 3])
