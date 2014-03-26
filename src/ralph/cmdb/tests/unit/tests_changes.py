# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from lxml import objectify
from mock import patch
import mock

from ralph.business.models import Venture, VentureRole
from ralph.cmdb.importer import CIImporter
from ralph.cmdb.integration.puppet import PuppetAgentsImporter
from ralph.cmdb.integration.puppet import PuppetGitImporter as pgi
from ralph.cmdb.models import (
    CI, CIChange, CI_TYPES, CIChangePuppet,
    CIChangeGit,
    CI_CHANGE_TYPES, CI_CHANGE_REGISTRATION_TYPES,
    GitPathMapping
)
from ralph.cmdb.models_changes import PuppetLog


CURRENT_DIR = settings.CURRENT_DIR
_PATCHED_OP_TEMPLATE = 'test'
_PATCHED_OP_START_DATE = datetime.date(2012, 1, 2)
_PATCHED_TICKETS_ENABLE = True
_PATCHED_ENQUEUE_REGISTRATION = False
_PATCHED_TICKETS_ENABLE_NO = False


class OPRegisterTest(TestCase):

    """Test creating OP changes and registering in the Issue Tracker"""

    def test_create_puppet_change(self):
        hostci = CI(name='s11401.dc2', uid='mm-1')
        hostci.type_id = CI_TYPES.DEVICE.id
        hostci.save()
        p = PuppetAgentsImporter()
        changed_yaml = open(
            os.path.join(CURRENT_DIR, 'cmdb/tests/samples/canonical.yaml'),
        ).read()
        p.import_contents(changed_yaml)
        unchanged_yaml = open(
            os.path.join(
                CURRENT_DIR, 'cmdb/tests/samples/canonical_unchanged.yaml'),
        ).read()
        p.import_contents(unchanged_yaml)
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
        # should drop request, when the same configuration ver. + hostname
        # is already present in the database.

        # Now, feed importer with the same yaml the second time...
        p.import_contents(changed_yaml)
        # No change should be registered at this time.
        self.assertEquals(
            chg, CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_AGENT.id)
        )
        self.assertEquals(
            CIChangePuppet.objects.count(), 1
        )

    @patch('ralph.cmdb.models_signals.OP_TEMPLATE', _PATCHED_OP_TEMPLATE)
    @patch('ralph.cmdb.models_signals.OP_START_DATE', _PATCHED_OP_START_DATE)
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE',
           _PATCHED_TICKETS_ENABLE)
    @patch('ralph.cmdb.models_signals.ENQUEUE_REGISTRATION', _PATCHED_ENQUEUE_REGISTRATION)
    def test_create_issues(self):
        # if change is registered after date of start, ticket is registered
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=2)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '#123456')
        self.assertEqual(
            chg.registration_type, CI_CHANGE_REGISTRATION_TYPES.OP.id)
        CIChange.objects.all().delete()

        # removing cichange remove cichangegit child too.
        self.assertEqual(CIChangeGit.objects.count(), 0)

        # if change is registered before date of start, and change type is GIT,
        # then ticket remains WAITING
        # forever. When date is changed, and signal is send to the model
        # ticket is going to be registrated again.
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=1)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '')
        self.assertEqual(
            chg.registration_type, CI_CHANGE_REGISTRATION_TYPES.WAITING.id)

    @patch('ralph.cmdb.models_signals.OP_TEMPLATE', _PATCHED_OP_TEMPLATE)
    @patch('ralph.cmdb.models_signals.OP_START_DATE', _PATCHED_OP_START_DATE)
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE',
           _PATCHED_TICKETS_ENABLE_NO)
    @patch('ralph.cmdb.models_signals.ENQUEUE_REGISTRATION', _PATCHED_ENQUEUE_REGISTRATION)
    def test_create_ci_generate_change(self):
        # TICKETS REGISTRATION IN THIS TEST IS DISABLED.
        # first case - automatic change
        hostci = CI(name='s11401.dc2', uid='mm-1')
        hostci.type_id = CI_TYPES.DEVICE.id
        hostci.save()
        # not registered, because not user - driven change
        self.assertEqual(
            set([(x.content_object.old_value,
                x.content_object.new_value, x.content_object.field_name,
                x.content_object.user_id, x.registration_type)
                for x in CIChange.objects.all()]),
            set([(u'None', u'Device', u'type', None,
                CI_CHANGE_REGISTRATION_TYPES.NOT_REGISTERED.id),
                (u'None', u'1', u'id', None,
                 CI_CHANGE_REGISTRATION_TYPES.NOT_REGISTERED.id)])
        )
        hostci.delete()
        # second case - manual change
        user = User.objects.create_user(
            'john', 'lennon@thebeatles.com', 'johnpassword')

        # john reigstered change, change should be at WAITING because
        # registering is not enabled in config
        hostci = CI(name='s11401.dc2', uid='mm-1')
        hostci.type_id = CI_TYPES.DEVICE.id
        hostci.save(user=user)
        self.assertEqual(
            set([(x.content_object.old_value,
                x.content_object.new_value, x.content_object.field_name,
                x.content_object.user_id, x.registration_type)
                for x in CIChange.objects.all()]),
            set([
                (u'None', u'Device', u'type', 1,
                    CI_CHANGE_REGISTRATION_TYPES.WAITING.id),
                (u'None', u'1', u'id', 1,
                    CI_CHANGE_REGISTRATION_TYPES.WAITING.id),
                ])
        )

    @patch('ralph.cmdb.models_signals.OP_TEMPLATE', _PATCHED_OP_TEMPLATE)
    @patch('ralph.cmdb.models_signals.OP_START_DATE', _PATCHED_OP_START_DATE)
    @patch('ralph.cmdb.models_signals.OP_TICKETS_ENABLE',
           _PATCHED_TICKETS_ENABLE_NO)
    @patch('ralph.cmdb.models_signals.ENQUEUE_REGISTRATION',
           _PATCHED_ENQUEUE_REGISTRATION)
    def test_dont_create_issues(self):
        # The date is ok, but tickets enabled is set to no.
        # Don't register tickets.
        c = CIChangeGit()
        c.time = datetime.datetime(year=2012, month=1, day=2)
        c.changeset = 'testchangeset'
        c.save()
        chg = CIChange.objects.get(type=CI_CHANGE_TYPES.CONF_GIT.id)
        # yeah, ticket is waiting, but not going to register because disabled
        # in config.
        self.assertEqual(chg.content_object, c)
        self.assertEqual(chg.external_key, '')
        self.assertEqual(
            chg.registration_type, CI_CHANGE_REGISTRATION_TYPES.WAITING.id)


class MockFisheye(object):

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return mock.Mock()

    def get_changes(self, *args, **kwargs):
        xml = open(
            os.path.join(CURRENT_DIR, 'cmdb',
                         'tests', 'samples', 'fisheye_changesets.xml'),
        ).read()
        return objectify.fromstring(xml)

    def get_details(self, *args, **kwargs):
        xml = open(
            os.path.join(CURRENT_DIR,
                         'cmdb', 'tests', 'samples', 'fisheye_details.xml'),
        ).read()
        return objectify.fromstring(xml)


class CIChangeGitTest(TestCase):

    """Create Venture/Role and import as CI/CIRelations.
    Import fisheye xml from samples/* files and save into the
    CIChangeGit objects.

    Git path mappings allows you to define what CI belongs to
    what path in the git changeset. You have 2 comparison functions
    for git mappers
    1. Simple
    2. Regex

    """

    def setUp(self):
        v = Venture(symbol='test_venture')
        v.save()
        r = VentureRole(name='test_role', venture=v)
        r.save()
        # ci for custom path mapping
        c = Venture(symbol='custom_ci', name='custom_ci')
        c.save()
        for i in (v, r, c):
            CIImporter().import_single_object(i)
            CIImporter().import_single_object_relations(i)

    def load_fisheye_data(self):
        # helper for importing xml data.
        with mock.patch(
                'ralph.cmdb.integration.lib.fisheye.Fisheye') as Fisheye:
            Fisheye.side_effect = MockFisheye
        x = pgi(fisheye_class=Fisheye)
        x.import_git()

    def test_fisheye_simple_mappings(self):
        """Check in string mapping"""
        GitPathMapping(
            is_regex=False,
            path='custom/test/file.xml',
            ci=CI.objects.get(name='custom_ci'),
        ).save()
        self.load_fisheye_data()
        self.assertEqual(CIChangeGit.objects.filter(
            ci__name='custom_ci').count(), 2)

    def test_fisheye_regex_mappings(self):
        """Check regex string mapping"""
        GitPathMapping(
            is_regex=True,
            path='.*custom.*regex.*\/file.xml',
            ci=CI.objects.get(name='custom_ci'),
        ).save()
        self.load_fisheye_data()
        self.assertEqual(CIChangeGit.objects.filter(
            ci__name='custom_ci').count(), 2)

    def test_fisheye_no_mappings(self):
        self.load_fisheye_data()
        self.assertEqual(CIChangeGit.objects.filter(
            author__contains='johny.test@test.pl',
        ).count(), 2)
        self.assertEqual(CIChange.objects.filter(
            ci__name='test_role',
            type=CI_CHANGE_TYPES.CONF_GIT.id,
        ).count(), 2)
