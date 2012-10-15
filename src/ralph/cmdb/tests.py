# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from os.path import join as djoin

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
import mock
from mock import patch
from lxml import objectify

from ralph.cmdb.importer import CIImporter
from ralph.cmdb.models import CI, CIRelation, CI_RELATION_TYPES, CIChange, CI_TYPES, \
    CIChangePuppet, CIChangeGit, CI_CHANGE_TYPES
from ralph.discovery.models import Device, DeviceType, DeviceModel
from ralph.business.models import Venture, VentureRole
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
            venturerole=self.child_role,
            sn='sn3',
            model=dm
        )
        self.blade.name = 'blade'
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
        ci_rack = CI.objects.get(name='rack')
        ci_blade = CI.objects.get(name='blade')
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
        # Relations count should be 6
        self.assertEqual(len(CIRelation.objects.all()), 6)


class JiraRssTest(TestCase):
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
    """ OP Changes such as git change, attribute change, is immiediatelly sent to
    issue tracker as CHANGE ticket for logging purporses. Check this workflow here
    """

    @patch('ralph.cmdb.models_signals.OP_TEMPLATE', _PATCHED_OP_TEMPLATE)
    @patch('ralph.cmdb.models_signals.OP_START_DATE', _PATCHED_OP_START_DATE)
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE', _PATCHED_TICKETS_ENABLE)
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

        # if change is registered before date of start, ticket is not registered
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
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE', _PATCHED_TICKETS_ENABLE_NO)
    @patch('ralph.cmdb.models_common.USE_CELERY', _PATCHED_USE_CELERY)
    def test_dont_create_issues(self):
        # the date is ok, but tickets enabled is set to no.  Dont register ticket.
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=2)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        # yeah, ticket is not registered, because disabled in config.
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '')
        self.assertEqual(chg.get_registration_type_display(), 'Not registered')
