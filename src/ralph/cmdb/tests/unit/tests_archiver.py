# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
import mock

from ralph.cmdb import archiver
from ralph.cmdb.models import (
    CI,
    CI_CHANGE_TYPES,
    CI_TYPES,
    CI_CHANGE_PRIORITY_TYPES,
    CIChange,
    ArchivedCIChange,
    CIChangeGit,
    ArchivedCIChangeGit,
    CIChangeZabbixTrigger,
    ArchivedCIChangeZabbixTrigger,
    CIChangeCMDBHistory,
    ArchivedCIChangeCMDBHistory,
    CIChangePuppet,
    ArchivedCIChangePuppet,
    PuppetLog,
    ArchivedPuppetLog,
)
from ralph.discovery.models import Device, DeviceType


class CMDBArchiverToolsTest(TestCase):

    def setUp(self):
        class Foo(models.Model):
            foo1 = models.CharField()
            foo2 = models.IntegerField()
        self.sampleDBModel = Foo

    def test_get_used_db_backend_name(self):
        db_backend = archiver._get_used_db_backend_name()
        self.assertTrue(
            db_backend in settings.DATABASES['default']['ENGINE'],
        )

    def test_get_db_columns_for_model(self):
        cols = archiver._get_db_columns_for_model(self.sampleDBModel)
        self.assertEqual(
            cols,
            ['id', 'foo1', 'foo2'],
        )

    def test_get_db_table_for_model(self):
        self.assertEqual(
            archiver._get_db_table_for_model(self.sampleDBModel),
            'unit_foo',
        )

    def test_make_advanced_delete_query(self):
        with mock.patch(
            'ralph.cmdb.archiver._get_used_db_backend_name'
        ) as db_backend:
            db_backend.return_value = 'mysql'
            sql = archiver._make_advanced_delete_query(
                self.sampleDBModel,
                self.sampleDBModel,
            )
            self.assertTrue(sql.lower().startswith(
                'delete unit_foo.* from unit_foo',
            ))
            db_backend.return_value = 'postgresql'
            sql = archiver._make_advanced_delete_query(
                self.sampleDBModel,
                self.sampleDBModel,
            )
            sql = ' '.join(sql.split())
            self.assertTrue(sql.lower().startswith(
                'delete from unit_foo using unit_foo',
            ))
            db_backend.return_value = 'sqlite'
            sql = archiver._make_advanced_delete_query(
                self.sampleDBModel,
                self.sampleDBModel,
            )
            sql = ' '.join(sql.split())
            self.assertTrue(sql.lower().startswith(
                'delete from unit_foo where unit_foo.id in (',
            ))
            self.assertRegexpMatches(
                sql.lower(),
                r'delete from (?P<tab>[a-z_]+) where (?P=tab)\.[a-z_]+ in',
            )


class CMDBArchiverTest(TestCase):

    def setUp(self):
        self._prepare_data_for_device_tests()
        self._prepare_data_for_git_tests()
        self._prepare_data_for_zabbix_tests()
        self._prepare_data_for_cmdb_tests()
        self._prepare_data_for_puppet_tests()

    def _prepare_data_for_device_tests(self):
        self.sample_device = Device.create(
            sn='sn_123456789_1',
            model_name='sampleDevice',
            model_type=DeviceType.unknown,
        )
        self.other_sample_device = Device.create(
            sn='sn_123456789_2',
            model_name='otherSampleDevice',
            model_type=DeviceType.unknown,
        )
        created = datetime.datetime.now() - datetime.timedelta(days=31)
        change = CIChange(
            type=CI_CHANGE_TYPES.DEVICE,
            content_type=ContentType.objects.get_for_model(
                self.sample_device,
            ),
            object_id=self.sample_device.id,
            created=created,
            priority=CI_CHANGE_PRIORITY_TYPES.ERROR,
        )
        change.save()
        self.cichange_device_id = change.id
        change = CIChange(
            type=CI_CHANGE_TYPES.DEVICE,
            content_type=ContentType.objects.get_for_model(
                self.other_sample_device,
            ),
            object_id=self.other_sample_device.id,
            created=created + datetime.timedelta(days=2),
            priority=CI_CHANGE_PRIORITY_TYPES.ERROR,
        )
        change.save()
        self.not_touched_cichange_device_id = change.id

    def _prepare_data_for_git_tests(self):
        git_change_1 = CIChangeGit(
            file_paths='path 1',
            comment='...',
            author='Arnold',
            changeset='123_1',
        )
        git_change_1.save()
        self.git_change_1_id = git_change_1.id
        change = CIChange.objects.get(
            type=CI_CHANGE_TYPES.CONF_GIT,
            content_type=ContentType.objects.get_for_model(git_change_1),
            object_id=self.git_change_1_id,
        )
        change.created = datetime.datetime.now() - datetime.timedelta(days=31)
        change.save()
        self.cichange_git_id = change.id
        git_change_2 = CIChangeGit(
            file_paths='path 2',
            comment='...',
            author='Arnold',
            changeset='123_2',
        )
        git_change_2.save()
        self.git_change_2_id = git_change_2.id
        change = CIChange.objects.get(
            type=CI_CHANGE_TYPES.CONF_GIT,
            content_type=ContentType.objects.get_for_model(git_change_2),
            object_id=self.git_change_2_id,
        )
        self.not_touched_cichange_git_id = change.id

    def _prepare_data_for_zabbix_tests(self):
        zabbix_change_1 = CIChangeZabbixTrigger(
            trigger_id=123,
            host='example.com',
            host_id=123,
            status=1,
            priority=1,
            description='...',
            lastchange='...',
            comments='...',
        )
        zabbix_change_1.save()
        self.zabbix_change_1_id = zabbix_change_1.id
        change = CIChange(
            type=CI_CHANGE_TYPES.ZABBIX_TRIGGER,
            content_type=ContentType.objects.get_for_model(zabbix_change_1),
            object_id=self.zabbix_change_1_id,
            created=datetime.datetime.now() - datetime.timedelta(days=31),
            priority=CI_CHANGE_PRIORITY_TYPES.ERROR,
        )
        change.save()
        self.cichange_zabbix_id = change.id
        zabbix_change_2 = CIChangeZabbixTrigger(
            trigger_id=321,
            host='host.com',
            host_id=321,
            status=1,
            priority=1,
            description='...',
            lastchange='...',
            comments='...',
        )
        zabbix_change_2.save()
        self.zabbix_change_2_id = zabbix_change_2.id
        change = CIChange(
            type=CI_CHANGE_TYPES.ZABBIX_TRIGGER,
            content_type=ContentType.objects.get_for_model(zabbix_change_2),
            object_id=self.zabbix_change_2_id,
            priority=CI_CHANGE_PRIORITY_TYPES.ERROR,
        )
        change.save()
        self.not_touched_cichange_zabbix_id = change.id

    def _prepare_data_for_cmdb_tests(self):
        self.sample_ci = CI.objects.create(
            uid='uid-ci1',
            type_id=CI_TYPES.DEVICE,
            barcode='barcodeci1',
            name='ciname1',
        )
        cmdb_change_1 = CIChangeCMDBHistory(
            ci=self.sample_ci,
            field_name='test1',
            old_value='a',
            new_value='b',
            comment='...',
        )
        cmdb_change_1.save()
        self.cmdb_change_1_id = cmdb_change_1.id
        change = CIChange.objects.get(
            type=CI_CHANGE_TYPES.CI,
            content_type=ContentType.objects.get_for_model(cmdb_change_1),
            object_id=self.cmdb_change_1_id,
        )
        change.created = datetime.datetime.now() - datetime.timedelta(days=31)
        change.save()
        self.cichange_cmdb_id = change.id
        cmdb_change_2 = CIChangeCMDBHistory(
            ci=self.sample_ci,
            field_name='test2',
            old_value='c',
            new_value='d',
            comment='...',
        )
        cmdb_change_2.save()
        self.cmdb_change_2_id = cmdb_change_2.id
        change = CIChange.objects.get(
            type=CI_CHANGE_TYPES.CI,
            content_type=ContentType.objects.get_for_model(cmdb_change_2),
            object_id=self.cmdb_change_2_id,
        )
        self.not_touched_cichange_cmdb_id = change.id

    def _prepare_data_for_puppet_tests(self):
        puppet_change_1 = CIChangePuppet(
            configuration_version='123_1',
            host='example.com',
            kind='...',
            status='not ok',
        )
        puppet_change_1.save()
        self.puppet_change_1_id = puppet_change_1.id
        puppet_log_1 = PuppetLog(
            source='...',
            message='...',
            tags='...',
            time=datetime.datetime.now() - datetime.timedelta(days=31),
            level='...',
            cichange=puppet_change_1,
        )
        puppet_log_1.save()
        self.puppet_log_1_id = puppet_log_1.id
        change = CIChange.objects.get(
            type=CI_CHANGE_TYPES.CONF_AGENT,
            content_type=ContentType.objects.get_for_model(puppet_change_1),
            object_id=self.puppet_change_1_id,
        )
        change.created = datetime.datetime.now() - datetime.timedelta(days=31)
        change.save()
        self.cichange_puppet_id = change.id
        puppet_change_2 = CIChangePuppet(
            configuration_version='123_2',
            host='example.com',
            kind='...',
            status='ok',
        )
        puppet_change_2.save()
        self.puppet_change_2_id = puppet_change_2.id
        puppet_log_2 = PuppetLog(
            source='...',
            message='...',
            tags='...',
            time=datetime.datetime.now() - datetime.timedelta(days=31),
            level='...',
            cichange=puppet_change_2,
        )
        puppet_log_2.save()
        self.puppet_log_2_id = puppet_log_2.id
        change = CIChange.objects.get(
            type=CI_CHANGE_TYPES.CONF_AGENT,
            content_type=ContentType.objects.get_for_model(puppet_change_2),
            object_id=self.puppet_change_2_id,
        )
        self.not_touched_cichange_puppet_id = change.id

    def test_run_cichange_device_archivization(self):
        archiver.run_cichange_device_archivization(
            datetime.datetime.now() - datetime.timedelta(days=30)
        )
        self.assertFalse(
            CIChange.objects.filter(pk=self.cichange_device_id).exists(),
        )
        self.assertTrue(
            ArchivedCIChange.objects.filter(
                pk=self.cichange_device_id,
            ).exists(),
        )
        self.assertTrue(
            CIChange.objects.filter(
                pk=self.not_touched_cichange_device_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChange.objects.filter(
                pk=self.not_touched_cichange_device_id,
            ).exists(),
        )

    def test_run_cichange_git_archivization(self):
        archiver.run_cichange_git_archivization(
            datetime.datetime.now() - datetime.timedelta(days=30)
        )
        self.assertFalse(
            CIChange.objects.filter(pk=self.cichange_git_id).exists(),
        )
        self.assertTrue(
            ArchivedCIChange.objects.filter(
                pk=self.cichange_git_id,
            ).exists(),
        )
        self.assertFalse(
            CIChangeGit.objects.filter(pk=self.git_change_1_id).exists(),
        )
        self.assertTrue(
            ArchivedCIChangeGit.objects.filter(
                pk=self.git_change_1_id,
            ).exists(),
        )
        self.assertTrue(
            CIChange.objects.filter(
                pk=self.not_touched_cichange_git_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChange.objects.filter(
                pk=self.not_touched_cichange_git_id,
            ).exists(),
        )
        self.assertTrue(
            CIChangeGit.objects.filter(pk=self.git_change_2_id).exists(),
        )
        self.assertFalse(
            ArchivedCIChangeGit.objects.filter(
                pk=self.git_change_2_id,
            ).exists(),
        )

    def test_run_cichange_zabbix_archivization(self):
        archiver.run_cichange_zabbix_archivization(
            datetime.datetime.now() - datetime.timedelta(days=30),
        )
        self.assertFalse(
            CIChange.objects.filter(pk=self.cichange_zabbix_id).exists(),
        )
        self.assertTrue(
            ArchivedCIChange.objects.filter(
                pk=self.cichange_zabbix_id,
            ).exists(),
        )
        self.assertFalse(
            CIChangeZabbixTrigger.objects.filter(
                pk=self.zabbix_change_1_id,
            ).exists(),
        )
        self.assertTrue(
            ArchivedCIChangeZabbixTrigger.objects.filter(
                pk=self.zabbix_change_1_id,
            ).exists(),
        )
        self.assertTrue(
            CIChange.objects.filter(
                pk=self.not_touched_cichange_zabbix_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChange.objects.filter(
                pk=self.not_touched_cichange_zabbix_id,
            ).exists(),
        )
        self.assertTrue(
            CIChangeZabbixTrigger.objects.filter(
                pk=self.zabbix_change_2_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChangeZabbixTrigger.objects.filter(
                pk=self.zabbix_change_2_id,
            ).exists(),
        )

    def test_run_cichange_cmdb_history_archivization(self):
        archiver.run_cichange_cmdb_history_archivization(
            datetime.datetime.now() - datetime.timedelta(days=30),
        )
        self.assertFalse(
            CIChange.objects.filter(pk=self.cichange_cmdb_id).exists(),
        )
        self.assertTrue(
            ArchivedCIChange.objects.filter(
                pk=self.cichange_cmdb_id,
            ).exists(),
        )
        self.assertFalse(
            CIChangeCMDBHistory.objects.filter(
                pk=self.cmdb_change_1_id,
            ).exists(),
        )
        self.assertTrue(
            ArchivedCIChangeCMDBHistory.objects.filter(
                pk=self.cmdb_change_1_id,
            ).exists(),
        )
        self.assertTrue(
            CIChange.objects.filter(
                pk=self.not_touched_cichange_cmdb_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChange.objects.filter(
                pk=self.not_touched_cichange_cmdb_id,
            ).exists(),
        )
        self.assertTrue(
            CIChangeCMDBHistory.objects.filter(
                pk=self.cmdb_change_2_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChangeCMDBHistory.objects.filter(
                pk=self.cmdb_change_2_id,
            ).exists(),
        )

    def test_run_cichange_puppet_archivization(self):
        archiver.run_cichange_puppet_archivization(
            datetime.datetime.now() - datetime.timedelta(days=30),
        )
        self.assertFalse(
            CIChange.objects.filter(pk=self.cichange_puppet_id).exists(),
        )
        self.assertTrue(
            ArchivedCIChange.objects.filter(
                pk=self.cichange_puppet_id,
            ).exists(),
        )
        self.assertFalse(
            CIChangePuppet.objects.filter(
                pk=self.puppet_change_1_id,
            ).exists(),
        )
        self.assertTrue(
            ArchivedCIChangePuppet.objects.filter(
                pk=self.puppet_change_1_id,
            ).exists(),
        )
        self.assertFalse(
            PuppetLog.objects.filter(
                pk=self.puppet_log_1_id,
            ).exists(),
        )
        self.assertTrue(
            ArchivedPuppetLog.objects.filter(
                pk=self.puppet_log_1_id,
            ).exists(),
        )
        self.assertTrue(
            CIChange.objects.filter(
                pk=self.not_touched_cichange_puppet_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChange.objects.filter(
                pk=self.not_touched_cichange_puppet_id,
            ).exists(),
        )
        self.assertTrue(
            CIChangePuppet.objects.filter(
                pk=self.puppet_change_2_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedCIChangePuppet.objects.filter(
                pk=self.puppet_change_2_id,
            ).exists(),
        )
        self.assertTrue(
            PuppetLog.objects.filter(
                pk=self.puppet_log_2_id,
            ).exists(),
        )
        self.assertFalse(
            ArchivedPuppetLog.objects.filter(
                pk=self.puppet_log_2_id,
            ).exists(),
        )
