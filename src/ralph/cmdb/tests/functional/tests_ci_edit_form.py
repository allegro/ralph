# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase, Client

from ralph.business.models import Venture, VentureRole
import ralph.cmdb.models as db
from ralph.discovery.models import Device, DeviceType


CURRENT_DIR = settings.CURRENT_DIR
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

        self.layer = db.CILayer(name='layer1')
        self.layer.save()
        self.citype = db.CIType(name='xxx')
        self.citype.save()

    def add_ci(self, name='CI', type=1):
        ci_add_url = '/cmdb/add/'
        attrs = {
            'base-layers': 1,
            'base-name': name,
            'base-state': 2,
            'base-status': 2,
            'base-type': type,
        }
        return self.client.post(ci_add_url, attrs)

    def edit_ci(self, ci, custom_attrs={}):
        ci_edit_url = '/cmdb/ci/edit/{}'.format(ci.id)
        attrs = {
            'base-name': ci.name,
            'base-type': 1,
            'base-state': 2,
            'base-status': 2,
            'base-layers': 1,
        }
        attrs.update(custom_attrs)
        return self.client.post(ci_edit_url, attrs)

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

    @skipIf(not settings.AUTOCI, settings.AUTOCI_SKIP_MSG)
    def test_add_two_ci_with_the_same_content_object(self):
        response = self.add_ci(name='CI')
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(IntegrityError) as e:
            ci = db.CI.objects.get(name='CI')
            ci.content_object = self.device
            ci.save()

    def test_two_ci_without_content_object(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI1')
        cis = db.CI.objects.filter(name='CI1')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        self.assertEqual(len(cis), 2)

    def test_add_ci_relation_rel_child(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        ci1 = db.CI.objects.get(name='CI1')
        ci2 = db.CI.objects.get(name='CI2')
        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_child',
            relation_kind=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id, child_id=ci2.id,
            type=db.CI_RELATION_TYPES.HASROLE)
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_child',
            relation_kind=db.CI_RELATION_TYPES.CONTAINS,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id,
            child_id=ci2.id,
            type=db.CI_RELATION_TYPES.CONTAINS,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.CONTAINS)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_child',
            relation_kind=db.CI_RELATION_TYPES.REQUIRES,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id, child_id=ci2.id,
            type=db.CI_RELATION_TYPES.REQUIRES
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.REQUIRES)

    def test_add_ci_relation_rel_parent(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        ci1 = db.CI.objects.get(name='CI1')
        ci2 = db.CI.objects.get(name='CI2')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.HASROLE
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id,
            child_id=ci2.id,
            type=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.CONTAINS,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id,
            child_id=ci2.id,
            type=db.CI_RELATION_TYPES.CONTAINS,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.CONTAINS)

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.REQUIRES,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id, child_id=ci2.id,
            type=db.CI_RELATION_TYPES.REQUIRES,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.REQUIRES)

    def test_add_circular_relation(self):
        response_ci = self.add_ci(name='CI')
        self.assertEqual(response_ci.status_code, 302)
        ci = db.CI.objects.get(name='CI')

        response_r = self.add_ci_relation(
            parent_ci=ci,
            child_ci=ci,
            relation_type='rel_child',
            relation_kind=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(response_r.context_data['form'].errors['__all__'][0],
                         'CI can not have relation with himself')

    def test_ci_cycle_parent_child(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)

        ci1 = db.CI.objects.get(name='CI1')
        ci2 = db.CI.objects.get(name='CI2')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(response_r.status_code, 302)
        response_r = self.add_ci_relation(
            parent_ci=ci2,
            child_ci=ci1,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.CONTAINS
        )
        self.assertEqual(response_r.status_code, 302)

    def test_ci_relations_cycle(self):
        response_ci1 = self.add_ci(name='CI1')
        response_ci2 = self.add_ci(name='CI2')
        response_ci3 = self.add_ci(name='CI3')
        self.assertEqual(response_ci1.status_code, 302)
        self.assertEqual(response_ci2.status_code, 302)
        self.assertEqual(response_ci3.status_code, 302)
        ci1 = db.CI.objects.get(name='CI1')
        ci2 = db.CI.objects.get(name='CI2')
        ci3 = db.CI.objects.get(name='CI3')

        response_r = self.add_ci_relation(
            parent_ci=ci1,
            child_ci=ci2,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci1.id,
            child_id=ci2.id,
            type=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci2,
            child_ci=ci3,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci2.id,
            child_id=ci3.id,
            type=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.HASROLE)

        response_r = self.add_ci_relation(
            parent_ci=ci3,
            child_ci=ci1,
            relation_type='rel_parent',
            relation_kind=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(response_r.status_code, 302)
        rel = db.CIRelation.objects.get(
            parent_id=ci3.id,
            child_id=ci1.id,
            type=db.CI_RELATION_TYPES.HASROLE,
        )
        self.assertEqual(rel.type, db.CI_RELATION_TYPES.HASROLE)

        cycle = db.CI.get_cycle()
        self.assertEqual(cycle, [ci1.id, ci2.id, ci3.id])

    def test_ci_custom_fields(self):
        # Create CI using the form, and edit custom float field.
        response_ci_application = self.add_ci(name='CI_application', type=1)
        self.assertEqual(response_ci_application.status_code, 302)
        ci_application = db.CI.objects.get(name='CI_application')
        response_ci_application_edit = self.edit_ci(
            ci_application, custom_attrs={
                'base-attribute_4': 12345
            }
        )
        self.assertEqual(response_ci_application_edit.status_code, 302)
        ci_attrvalue = ci_application.ciattributevalue_set.all()
        values = {}
        values['float'] = [value.value_float_id for value in ci_attrvalue
                           if value.value_float]
        ci_values = db.CIValueFloat.objects.get(id__in=values['float'])
        self.assertEqual(ci_values.value, 12345)

        # Create CI using the form, and edit custom date & float fields.
        response_ci_device = self.add_ci(name='CI_device', type=2)
        self.assertEqual(response_ci_device.status_code, 302)
        ci_device = db.CI.objects.get(name='CI_device')
        response_ci_device_edit = self.edit_ci(
            ci_device, custom_attrs={
                'base-attribute_3': time.strftime('%Y-%m-%d'),
                'base-attribute_4': 666,
            }
        )
        self.assertEqual(response_ci_device_edit.status_code, 302)
        ci_attrvalue = ci_device.ciattributevalue_set.all()
        values = {}
        values['float'] = [value.value_float_id for value in ci_attrvalue
                           if value.value_float]
        values['date'] = [value.value_date_id for value in ci_attrvalue
                          if value.value_date]
        ci_float_value = db.CIValueFloat.objects.get(id__in=values['float'])
        ci_date_value = db.CIValueDate.objects.get(id__in=values['date'])
        self.assertEqual(ci_date_value.value.strftime('%Y-%m-%d'),
                         time.strftime('%Y-%m-%d'))
        self.assertEqual(ci_float_value.value, 666)

        # Create CI using the form, and edit custom string field.
        response_ci_device = self.add_ci(name='CI_procedure', type=3)
        self.assertEqual(response_ci_device.status_code, 302)
        ci_device = db.CI.objects.get(name='CI_procedure')
        response_ci_device_edit = self.edit_ci(
            ci_device, custom_attrs={
                'base-attribute_1': 'http://doc.local',
                'base-attribute_2': 'name-test',
            }
        )
        self.assertEqual(response_ci_device_edit.status_code, 302)
        ci_attrvalue = ci_device.ciattributevalue_set.all()
        values = {}
        values['string'] = [value.value_string_id for value in ci_attrvalue
                            if value.value_string]
        ci_string_value = db.CIValueString.objects.filter(
            pk__in=values['string']
        )
        val = [value.value for value in ci_string_value]
        val.sort()
        self.assertListEqual(val, ['http://doc.local', 'name-test'])
