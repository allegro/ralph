# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from tastypie.bundle import Bundle
from tastypie.models import ApiKey

from ralph.business.models import Venture
from ralph.cmdb import models as chdb
from ralph.cmdb.api import (
    CIChangePuppetResource, CIChangeGitResource, CIChangeCMDBHistoryResource,
)
from ralph.cmdb.models import (
    CIChangePuppet, CIChangeGit, CIChangeCMDBHistory, CIChange,
    CIOwnershipType
)
from ralph.cmdb.models import (
    CILayer, CI_RELATION_TYPES,
)
from ralph.cmdb.models_ci import CIOwnership, CI, CIOwner, CIType, CIRelation

CURRENT_DIR = settings.CURRENT_DIR


class CMDBApiTest(TestCase):
    def setUp(self):
        self.create_user()
        self.layers = CILayer.objects.all()
        self.types = CIType.objects.all()
        self.create_owners()
        self.create_cis()
        self.create_ownerships()
        self.create_relations()

    def create_user(self):
        self.user = User.objects.create_user(
            'api_user',
            'test@mail.local',
            'password'
        )
        self.user.save()
        self.api_key = ApiKey.objects.get(user=self.user)
        self.data = {
            'format': 'json',
            'username': self.user.username,
            'api_key': self.api_key.key
        }
        cache.delete("api_user_accesses")

    def create_owners(self):
        self.owner1 = CIOwner(
            first_name='first_name_owner1',
            last_name='last_name_owner1',
            email='first_name_owner1.last_name_owner1@ralph.local'
        )
        self.owner1.save()
        self.owner2 = CIOwner(
            first_name='first_name_owner2',
            last_name='last_name_owner2',
            email='first_name_owner2.last_name_owner2@ralph.local'
        )
        self.owner2.save()

    def create_cis(self):
        self.ci1 = CI(
            uid='uid-ci1',
            type=self.types[0],
            barcode='barcodeci1',
            name='ciname1',
        )
        self.ci1.save()
        self.ci1.layers = [self.layers[0].id, self.layers[1].id]
        self.ci1.save()
        self.ci2 = CI(
            uid='uid-ci2',
            type=self.types[1],
            barcode='barcodeci2',
            name='ciname2',
        )
        self.ci2.save()
        self.ci2.layers = [self.layers[0].id]
        self.ci2.save()
        self.ci3 = CI(
            uid='other-ci3',
            type=self.types[1],
            barcode='otherbarcodeci3',
            name='otherci',
        )
        self.ci3.save()
        self.ci3.layers = [self.layers[1].id]
        self.ci3.save()

    def create_ownerships(self):
        self.ciownership1 = CIOwnership(
            ci=self.ci1,
            owner=self.owner1,
            type=CIOwnershipType.technical
        )
        self.ciownership1.save()
        self.ciownership2 = CIOwnership(
            ci=self.ci1,
            owner=self.owner2,
            type=CIOwnershipType.business
        )
        self.ciownership2.save()
        self.ciownership3 = CIOwnership(
            ci=self.ci2,
            owner=self.owner2,
            type=CIOwnershipType.business
        )
        self.ciownership3.save()

    def create_relations(self):
        self.relation1 = CIRelation(
            parent=self.ci1,
            child=self.ci2,
            type=CI_RELATION_TYPES.CONTAINS,
        )
        self.relation1.save()
        self.relation2 = CIRelation(
            parent=self.ci2,
            child=self.ci3,
            type=CI_RELATION_TYPES.HASROLE,
        )
        self.relation2.save()

    def test_layers(self):
        path = "/api/v0.9/cilayers/"
        response = self.client.get(path=path, data=self.data, format='json')
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [x['resource_uri'] for x in json_data['objects']]

        response = self.client.get(
            path=resource_uris[0], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['name'], self.layers[0].name)

        response = self.client.get(
            path=resource_uris[1], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['name'], self.layers[1].name)

    def test_types(self):
        path = "/api/v0.9/citypes/"
        response = self.client.get(path=path, data=self.data, format='json')
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [x['resource_uri'] for x in json_data['objects']]

        response = self.client.get(
            path=resource_uris[0], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)

        self.assertEqual(json_data['name'], self.types[0].name)

        response = self.client.get(
            path=resource_uris[1], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['name'], self.types[1].name)

    def test_ci(self):
        path = "/api/v0.9/ci/"
        response = self.client.get(path=path, data=self.data, format='json')
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [x['resource_uri'] for x in json_data['objects']]

        response = self.client.get(
            path=resource_uris[0], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['layers'][1]['name'], self.layers[1].name)
        self.assertEqual(json_data['barcode'], self.ci1.barcode)
        self.assertEqual(json_data['name'], self.ci1.name)
        self.assertEqual(json_data['type']['name'], self.ci1.type.name)
        self.assertEqual(json_data['uid'], self.ci1.uid)
        self.assertEqual(
            json_data['technical_owners'][0]['username'],
            '{}.{}'.format(self.owner1.first_name, self.owner1.last_name)
        )
        self.assertEqual(
            json_data['business_owners'][0]['username'],
            '{}.{}'.format(self.owner2.first_name, self.owner2.last_name)
        )

        response = self.client.get(
            path=resource_uris[1], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['barcode'], self.ci2.barcode)
        self.assertEqual(json_data['name'], self.ci2.name)
        self.assertEqual(json_data['type']['name'], self.ci2.type.name)
        self.assertEqual(json_data['uid'], self.ci2.uid)
        self.assertFalse(json_data['technical_owners'])
        self.assertEqual(
            json_data['business_owners'][0]['username'],
            '{}.{}'.format(self.owner2.first_name, self.owner2.last_name)
        )

    def test_relations(self):
        path = "/api/v0.9/cirelation/"
        response = self.client.get(path=path, data=self.data, format='json')
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [x['resource_uri'] for x in json_data['objects']]

        response = self.client.get(
            path=resource_uris[0], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['parent'], self.ci1.id)
        self.assertEqual(json_data['child'], self.ci2.id)
        self.assertEqual(json_data['type'], CI_RELATION_TYPES.CONTAINS)

        response = self.client.get(
            path=resource_uris[1], data=self.data, format='json',
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['parent'], self.ci2.id)
        self.assertEqual(json_data['child'], self.ci3.id)
        self.assertEqual(json_data['type'], CI_RELATION_TYPES.HASROLE)

    def test_ci_filter_exact(self):
        path = "/api/v0.9/ci/"
        self.data['name__exact'] = 'otherci'
        response = self.client.get(path=path, data=self.data, format='json')
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [x['resource_uri'] for x in json_data['objects']]
        self.assertEqual(len(resource_uris), 1)
        response = self.client.get(
            path=resource_uris[0], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[1].name)
        self.assertEqual(json_data['barcode'], self.ci3.barcode)
        self.assertEqual(json_data['name'], self.ci3.name)
        self.assertEqual(json_data['type']['name'], self.ci3.type.name)
        self.assertEqual(json_data['uid'], self.ci3.uid)
        del(self.data['name__exact'])

    def test_ci_filter_startswith(self):
        path = "/api/v0.9/ci/"
        self.data['name__startswith'] = 'ciname'
        response = self.client.get(path=path, data=self.data, format='json')
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [x['resource_uri'] for x in json_data['objects']]
        self.assertEqual(len(resource_uris), 2)
        response = self.client.get(
            path=resource_uris[0], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['barcode'], self.ci1.barcode)
        self.assertEqual(json_data['name'], self.ci1.name)
        self.assertEqual(json_data['type']['name'], self.ci1.type.name)
        self.assertEqual(json_data['uid'], self.ci1.uid)

        response = self.client.get(
            path=resource_uris[1], data=self.data, format='json'
        )
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['barcode'], self.ci2.barcode)
        self.assertEqual(json_data['name'], self.ci2.name)
        self.assertEqual(json_data['type']['name'], self.ci2.type.name)
        self.assertEqual(json_data['uid'], self.ci2.uid)

        del(self.data['name__startswith'])


class CIApiTest(TestCase):
    def setUp(self):
        self.puppet_cv = "v%s" % random.randrange(0, 1000)
        puppet_bundle = Bundle(
            data={
                'configuration_version': self.puppet_cv,
                'host': 's11111.dc2',
                'kind': 'apply',
                'status': 'failed',
                'time': '2012-11-14 13:00:00'
            })
        puppet_resource = CIChangePuppetResource()
        puppet_resource.obj_create(bundle=puppet_bundle)

        self.git_changeset = "change:%s" % random.randrange(0, 1000)
        self.git_comment = "comment:%s" % random.randrange(0, 1000)
        git_bundle = Bundle(
            data={
                'author': 'Jan Kowalski',
                'changeset': self.git_changeset,
                'comment': self.git_comment,
                'file_paths': '/some/path',
            })
        git_resource = CIChangeGitResource()
        git_resource.obj_create(bundle=git_bundle)

        temp_venture = Venture.objects.create(name='TempTestVenture')
        if settings.AUTOCI:
            self.ci = CI.objects.all()[0]
        else:
            self.ci = CI.objects.create(
            name='TempTestVentureCI',
            uid=CI.get_uid_by_content_object(temp_venture),
            type_id=4
        )

        self.cmdb_new_value = 'nv_%s' % random.randrange(0, 1000)
        self.cmdb_old_value = 'ov_%s' % random.randrange(0, 1000)
        cmdb_bundle = Bundle(
            data={
                'ci': '/api/v0.9/ci/%d/' % self.ci.pk,
                'comment': 'test api',
                'field_name': 'child',
                'new_value': self.cmdb_new_value,
                'old_value': self.cmdb_old_value,
                'time': '2012-11-15 12:00:00'
            })
        cmdb_resource = CIChangeCMDBHistoryResource()
        cmdb_resource.obj_create(bundle=cmdb_bundle)

    def test_ci_change_puppet_registration(self):
        puppet_change = None
        try:
            puppet_change = CIChangePuppet.objects.get(
                host='s11111.dc2', configuration_version=self.puppet_cv)
        except CIChangePuppet.DoesNotExist:
            pass
        self.assertNotEqual(puppet_change, None)
        self.assertEqual(puppet_change.kind, 'apply')
        self.assertEqual(puppet_change.status, 'failed')
        self.assertEqual(
            CIChange.objects.filter(
                object_id=puppet_change.id,
                type=chdb.CI_CHANGE_TYPES.CONF_AGENT.id).count(), 1)

    def test_ci_change_git_registration(self):
        git_change = None
        try:
            git_change = CIChangeGit.objects.get(changeset=self.git_changeset,
                                                 comment=self.git_comment)
        except CIChangePuppet.DoesNotExist:
            pass
        self.assertNotEqual(git_change, None)
        self.assertEqual(git_change.author, 'Jan Kowalski')
        self.assertEqual(git_change.file_paths, '/some/path')
        self.assertEqual(
            CIChange.objects.filter(
                object_id=git_change.id,
                type=chdb.CI_CHANGE_TYPES.CONF_GIT.id).count(), 1)

    def test_ci_change_cmdbhistory_registration(self):
        cmdb_change = None
        try:
            cmdb_change = CIChangeCMDBHistory.objects.get(
                ci_id=self.ci.id, old_value=self.cmdb_old_value,
                new_value=self.cmdb_new_value)
        except CIChangeCMDBHistory.DoesNotExist:
            pass
        self.assertNotEqual(cmdb_change, None)
        self.assertEqual(
            CIChange.objects.filter(
                object_id=cmdb_change.id,
                type=chdb.CI_CHANGE_TYPES.CI.id).count(), 1)
