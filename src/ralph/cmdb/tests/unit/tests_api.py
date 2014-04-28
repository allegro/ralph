# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import random

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import FakePayload
from tastypie.bundle import Bundle

from ralph.account. models import BoundPerm, Profile, Perm
from ralph.business.models import Venture
from ralph.cmdb import models as chdb
from ralph.cmdb.api import CIChangeCMDBHistoryResource
from ralph.cmdb.importer import CIImporter
from ralph.cmdb.models import (
    CIChangePuppet,
    CIChangeGit,
    CIChangeCMDBHistory,
    CIChange,
    CILayer,
    CIAttribute,
    CIAttributeValue,
    CI_RELATION_TYPES,
    CI_ATTRIBUTE_TYPES,
)
from ralph.cmdb.models_ci import (
    CIOwnershipType,
    CIOwnership,
    CI,
    CIOwner,
    CIType,
    CIRelation,
)
from ralph.ui.tests.global_utils import create_user

CURRENT_DIR = settings.CURRENT_DIR


class CMDBApiTest(TestCase):

    def setUp(self):
        self.user = create_user('api_user', 'test@mail.local', 'password')
        self.layers = CILayer.objects.all()
        self.types = CIType.objects.all()
        self.create_owners()
        self.create_cis()
        self.create_ownerships()
        self.create_attributes()
        self.create_relations()
        self.headers = {
            'HTTP_ACCEPT': 'application/json',
            'HTTP_AUTHORIZATION': 'ApiKey {}:{}'.format(
                self.user.username, self.user.api_key.key
            ),
        }
        cache.delete("api_user_accesses")

    def create_owners(self):
        self.owner1 = CIOwner(
            first_name='first_name_owner1',
            last_name='last_name_owner1',
            email='first_name_owner1.last_name_owner1@ralph.local',
        )
        self.owner1.save()
        self.owner2 = CIOwner(
            first_name='first_name_owner2',
            last_name='last_name_owner2',
            email='first_name_owner2.last_name_owner2@ralph.local',
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
            type=CIOwnershipType.technical,
        )
        self.ciownership1.save()
        self.ciownership2 = CIOwnership(
            ci=self.ci1,
            owner=self.owner2,
            type=CIOwnershipType.business,
        )
        self.ciownership2.save()
        self.ciownership3 = CIOwnership(
            ci=self.ci2,
            owner=self.owner2,
            type=CIOwnershipType.business,
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

    def create_attributes(self):
        self.attribute1 = CIAttribute(
            name='Attribute 1', attribute_type=CI_ATTRIBUTE_TYPES.INTEGER,
            choices='',
        )
        self.attribute1.save()
        self.attribute1.ci_types.add(self.types[0]),
        self.attribute_value1 = CIAttributeValue(
            ci=self.ci1, attribute=self.attribute1,
        )
        self.attribute_value1.value = 10
        self.attribute_value1.save()

    def test_layers(self):
        path = "/api/v0.9/cilayers/"
        response = self.client.get(path=path, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [
            ci_layer['resource_uri'] for ci_layer in json_data['objects']
        ]

        response = self.client.get(path=resource_uris[0], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['name'], self.layers[0].name)

        response = self.client.get(resource_uris[1], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['name'], self.layers[1].name)

    def test_types(self):
        path = "/api/v0.9/citypes/"
        response = self.client.get(path=path, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [
            ci_type['resource_uri'] for ci_type in json_data['objects']
        ]
        response = self.client.get(path=resource_uris[0], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)

        self.assertEqual(json_data['name'], self.types[0].name)

        response = self.client.get(resource_uris[1], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['name'], self.types[1].name)

    def test_ci(self):
        path = "/api/v0.9/ci/"
        response = self.client.get(path, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [ci['resource_uri'] for ci in json_data['objects']]

        response = self.client.get(resource_uris[0], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['layers'][1]['name'], self.layers[1].name)
        self.assertEqual(json_data['barcode'], self.ci1.barcode)
        self.assertEqual(json_data['name'], self.ci1.name)
        self.assertEqual(json_data['type']['name'], self.ci1.type.name)
        self.assertEqual(json_data['uid'], self.ci1.uid)
        self.assertEqual(
            json_data['technical_owners'][0]['first_name'],
            self.owner1.first_name,
        )
        self.assertEqual(
            json_data['business_owners'][0]['first_name'],
            self.owner2.first_name,
        )

        response = self.client.get(resource_uris[1], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['barcode'], self.ci2.barcode)
        self.assertEqual(json_data['name'], self.ci2.name)
        self.assertEqual(json_data['type']['name'], self.ci2.type.name)
        self.assertEqual(json_data['uid'], self.ci2.uid)
        self.assertFalse(json_data['technical_owners'])
        self.assertEqual(
            json_data['business_owners'][0]['first_name'],
            self.owner2.first_name,
        )

    def test_ownership(self):
        """Test the direct and effective ownerships."""
        path1 = '/api/v0.9/ci/{}/'.format(self.ci1.id)
        path3 = '/api/v0.9/ci/{}/'.format(self.ci3.id)
        ci1_data = json.loads(self.client.get(path1, **self.headers).content)
        ci3_data = json.loads(self.client.get(path3, **self.headers).content)
        # CI1 has its own owners
        self.assertListEqual(
            ci1_data['business_owners'],
            ci1_data['effective_business_owners']
        )
        # CI3 inherits owners from CI1
        self.assertListEqual(ci3_data['business_owners'], [])
        self.assertListEqual(
            ci3_data['effective_business_owners'],
            ci1_data['business_owners']
        )

    def test_post_ci(self):
        """POST to ci collection should create a new CI"""
        ci_count_before = CI.objects.count()
        ci_data = json.dumps({
            'uid': 'uid-ci-api-1',
            'type': '/api/v0.9/citypes/{0}/'.format(self.types[0].id),
            'barcode': 'barcodeapi1',
            'name': 'ciname from api 1',
            'layers': ['/api/v0.9/cilayers/5/'],
            'business_owners': [
                '/api/v0.9/ciowners/{0}/'.format(self.owner1.id)
            ],
            'technical_owners': [
                '/api/v0.9/ciowners/{0}/'.format(self.owner2.id)
            ],
            'attributes': [
                {
                    'name': 'SLA value',
                    'value': 0.7,
                }, {
                    'name': 'Documentation Link',
                    'value': 'http://www.gutenberg.org/files/27827/'
                    '27827-h/27827-h.htm',
                },
            ],
        })
        resp = self.client.post(
            '/api/v0.9/ci/?',
            ci_data,
            content_type='application/json',
            **self.headers
        )
        self.assertEqual(CI.objects.count(), ci_count_before + 1)
        created_id = int(resp['Location'].split('/')[-2])
        created = CI.objects.get(pk=created_id)
        self.assertEqual(created.name, 'ciname from api 1')
        self.assertSetEqual(
            set(created.business_owners.all()),
            {self.owner1},
        )
        self.assertSetEqual(
            set(av.value for av in created.ciattributevalue_set.all()),
            {
                0.7,
                'http://www.gutenberg.org/files/27827/27827-h/27827-h.htm',
            },
        )

    def test_put_ci(self):
        """PUT should edit existing CI"""
        ci_count_before = CI.objects.count()
        ci_data = json.dumps({
            'uid': 'uid-ci-api-1',
            'type': '/api/v0.9/citypes/{0}/'.format(self.types[0].id),
            'barcode': 'barcodeapi1',
            'name': 'ciname from api 1',
            'layers': ['/api/v0.9/cilayers/5/'],
            'business_owners': [
                '/api/v0.9/ciowners/{0}/'.format(self.owner1.id)
            ],
            'technical_owners': [
                '/api/v0.9/ciowners/{0}/'.format(self.owner2.id)
            ],
            'attributes': [
                {
                    'name': 'SLA value',
                    'value': 0.7,
                }, {
                    'name': 'Documentation Link',
                    'value': 'http://www.gutenberg.org/files/27827/'
                    '27827-h/27827-h.htm',
                },
            ],
        })
        self.client.put(
            '/api/v0.9/ci/{0}/'.format(
                self.ci1.id,
            ),
            ci_data,
            content_type='application/json',
            **self.headers
        )
        self.assertEqual(CI.objects.count(), ci_count_before)
        edited = CI.objects.get(pk=self.ci1.id)
        self.assertEqual(edited.name, 'ciname from api 1')
        self.assertSetEqual(
            set(edited.business_owners.all()),
            {self.owner1},
        )
        self.assertSetEqual(
            set(av.value for av in edited.ciattributevalue_set.all()),
            {
                0.7,
                'http://www.gutenberg.org/files/27827/27827-h/27827-h.htm',
            },
        )

    def test_patch(self):
        """PATCH should edit some attributes."""
        ci_count_before = CI.objects.count()
        ci_data = json.dumps({
            'business_owners': [
                '/api/v0.9/ciowners/{0}/'.format(self.owner1.id)
            ],
            'technical_owners': [
                '/api/v0.9/ciowners/{0}/'.format(self.owner2.id)
            ],
            'attributes': [
                {
                    'name': 'SLA value',
                    'value': 0.7,
                }, {
                    'name': 'Documentation Link',
                    'value': 'http://www.gutenberg.org/files/27827/'
                    '27827-h/27827-h.htm',
                },
            ],
        })
        req_data = {
            'CONTENT_LENGTH': len(ci_data),
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/api/v0.9/ci/{0}/'.format(self.ci1.id),
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input': FakePayload(ci_data),
        }
        req_data.update(self.headers)
        self.client.request(**req_data)
        self.assertEqual(CI.objects.count(), ci_count_before)
        edited = CI.objects.get(pk=self.ci1.id)
        self.assertEqual(edited.name, 'ciname1')
        self.assertEqual(edited.uid, 'uid-ci1')
        self.assertSetEqual(
            set(edited.business_owners.all()),
            {self.owner1},
        )
        self.assertSetEqual(
            set(av.value for av in edited.ciattributevalue_set.all()),
            {
                0.7,
                'http://www.gutenberg.org/files/27827/27827-h/27827-h.htm',
            },
        )

    def test_get_attribute(self):
        path = "/api/v0.9/ci/{0}/".format(self.ci1.id)
        response = self.client.get(path, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertListEqual(json_data['attributes'], [
            {'name': 'Attribute 1', 'value': 10}
        ])

    def test_relations(self):
        path = "/api/v0.9/cirelation/"
        response = self.client.get(path, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [
            ci_relation['resource_uri'] for ci_relation in json_data['objects']
        ]

        response = self.client.get(resource_uris[0], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['parent'], self.ci1.id)
        self.assertEqual(json_data['child'], self.ci2.id)
        self.assertEqual(json_data['type'], CI_RELATION_TYPES.CONTAINS)

        response = self.client.get(resource_uris[1], **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['parent'], self.ci2.id)
        self.assertEqual(json_data['child'], self.ci3.id)
        self.assertEqual(json_data['type'], CI_RELATION_TYPES.HASROLE)

    def test_ci_filter_exact(self):
        path = "/api/v0.9/ci/"
        data = {'name__exact': 'otherci'}
        response = self.client.get(path, data=data, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [ci['resource_uri'] for ci in json_data['objects']]
        self.assertEqual(len(resource_uris), 1)
        response = self.client.get(resource_uris[0], data, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[1].name)
        self.assertEqual(json_data['barcode'], self.ci3.barcode)
        self.assertEqual(json_data['name'], self.ci3.name)
        self.assertEqual(json_data['type']['name'], self.ci3.type.name)
        self.assertEqual(json_data['uid'], self.ci3.uid)

    def test_ci_filter_startswith(self):
        path = "/api/v0.9/ci/"
        data = {'name__startswith': 'ciname'}
        response = self.client.get(path=path, data=data, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        resource_uris = [ci['resource_uri'] for ci in json_data['objects']]
        self.assertEqual(len(resource_uris), 2)
        response = self.client.get(resource_uris[0], data=data, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['barcode'], self.ci1.barcode)
        self.assertEqual(json_data['name'], self.ci1.name)
        self.assertEqual(json_data['type']['name'], self.ci1.type.name)
        self.assertEqual(json_data['uid'], self.ci1.uid)

        response = self.client.get(resource_uris[1], data=data, **self.headers)
        json_string = response.content
        json_data = json.loads(json_string)
        self.assertEqual(json_data['layers'][0]['name'], self.layers[0].name)
        self.assertEqual(json_data['barcode'], self.ci2.barcode)
        self.assertEqual(json_data['name'], self.ci2.name)
        self.assertEqual(json_data['type']['name'], self.ci2.type.name)
        self.assertEqual(json_data['uid'], self.ci2.uid)


class CIApiTest(TestCase):

    def setUp(self):
        self.user = create_user(
            'api_user',
            'test@mail.local',
            'password',
            is_superuser=True
        )
        self.puppet_cv = "v%s" % random.randrange(0, 1000)
        self.post_data_puppet = {
            'configuration_version': self.puppet_cv,
            'host': 's11111.dc2',
            'kind': 'apply',
            'status': 'failed',
            'time': '2012-11-14 13:00:00',
        }

        self.git_changeset = "change:%s" % random.randrange(0, 1000)
        self.git_comment = "comment:%s" % random.randrange(0, 1000)
        self.post_data_git = {
            'author': 'Jan Kowalski',
            'changeset': self.git_changeset,
            'comment': self.git_comment,
            'file_paths': '/some/path',
        }

        temp_venture = Venture.objects.create(name='TempTestVenture')
        if settings.AUTOCI:
            self.ci = CI.get_by_content_object(temp_venture)
        else:
            CIImporter().import_single_object(temp_venture)
            self.ci = CI.objects.create(
                name='TempTestVentureCI',
                uid=CI.get_uid_by_content_object(temp_venture),
                type_id=4,
            )

        self.cmdb_new_value = 'nv_%s' % random.randrange(0, 1000)
        self.cmdb_old_value = 'ov_%s' % random.randrange(0, 1000)
        self.post_data_cmdb_change = {
            'ci': '/api/v0.9/ci/%d/' % self.ci.pk,
            'comment': 'test api',
            'field_name': 'child',
            'new_value': self.cmdb_new_value,
            'old_value': self.cmdb_old_value,
            'time': '2012-11-15 12:00:00',
        }
        cache.clear()

    def test_ci_change_puppet_registration(self):
        response = self.client.post(
            '/api/v0.9/cichangepuppet/?username={}&api_key={}'.format(
                self.user.username,
                self.user.api_key.key,
            ),
            json.dumps(self.post_data_puppet),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
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
        response = self.client.post(
            '/api/v0.9/cichangegit/?username={}&api_key={}'.format(
                self.user.username,
                self.user.api_key.key,
            ),
            json.dumps(self.post_data_git),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
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
                type=chdb.CI_CHANGE_TYPES.CONF_GIT.id,
            ).count(),
            1,
        )

    def test_ci_change_cmdbhistory_registration(self):
        request = HttpRequest()
        request.path = self.post_data_cmdb_change['ci']
        request.user = self.user
        request.META['SERVER_NAME'] = 'testserver'
        request.META['SERVER_PORT'] = 80

        cmdb_bundle = Bundle(data=self.post_data_cmdb_change, request=request)
        cmdb_resource = CIChangeCMDBHistoryResource()
        cmdb_resource.obj_create(bundle=cmdb_bundle)

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
                type=chdb.CI_CHANGE_TYPES.CI.id
            ).count(),
            1,
        )


class AccessToCMDBApiTest(TestCase):

    def setUp(self):
        self.user = create_user(
            'api_user',
            'test@mail.local',
            'password',
            is_staff=False,
            is_superuser=False,
        )
        self.api_login = {
            'format': 'json',
            'username': self.user.username,
            'api_key': self.user.api_key.key,
        }
        cache.delete("api_user_accesses")

    def get_response(self, resource):
        path = "/api/v0.9/%s/" % resource
        response = self.client.get(
            path=path,
            data=self.api_login,
            format='json',
        )
        return response

    def add_perms(self, perms):
        user_profile = Profile.objects.get(user=self.user)
        for perm in perms:
            BoundPerm(profile=user_profile, perm=perm).save()

    def test_businessline_resource(self):
        resource = 'businessline'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_service_resource(self):
        resource = 'service'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cirelation_resource(self):
        resource = 'cirelation'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_ci_resource(self):
        resource = 'ci'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cilayers_resource(self):
        resource = 'cilayers'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cichange_resource(self):
        resource = 'cichange'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cichangezabbixtrigger_resource(self):
        resource = 'cichangezabbixtrigger'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cichangegit_resource(self):
        resource = 'cichangegit'
        perms = [Perm.read_configuration_item_info_git]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cichangepuppet_resource(self):
        resource = 'cichangepuppet'
        perms = [Perm.read_configuration_item_info_puppet]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_cichangecmdbhistory_resource(self):
        resource = 'cichangecmdbhistory'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_citypes_resource(self):
        resource = 'citypes'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)

    def test_ciowners_resource(self):
        resource = 'ciowners'
        perms = [Perm.read_configuration_item_info_generic]

        schema = '%s/schema' % resource
        response = self.get_response(schema)
        self.assertEqual(response.status_code, 200)

        response = self.get_response(resource)
        self.assertEqual(response.status_code, 401)

        # Add perms to display resources
        self.add_perms(perms=perms)
        response = self.get_response(resource)
        self.assertEqual(response.status_code, 200)
