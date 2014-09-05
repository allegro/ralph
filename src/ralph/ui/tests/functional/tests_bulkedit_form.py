# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from factory import fuzzy, Sequence, SubFactory
from factory.django import DjangoModelFactory

from ralph.business.models import Venture, VentureRole
from ralph.discovery.models_device import Device
from ralph.discovery.models_history import HistoryChange
from ralph.ui.tests.global_utils import login_as_su


class VentureFactory(DjangoModelFactory):
    FACTORY_FOR = Venture
    name = Sequence(lambda n: 'Venture #{}'.format(n))


class VentureRoleFactory(DjangoModelFactory):
    FACTORY_FOR = VentureRole
    name = Sequence(lambda n: 'Venture role #{}'.format(n))
    venture = SubFactory(VentureFactory)


class ParentDeviceFactory(DjangoModelFactory):
    FACTORY_FOR = Device
    verified = False
    name = Sequence(lambda n: 'Parent device #{}'.format(n))
    venture = SubFactory(VentureFactory)
    venture_role = SubFactory(VentureRoleFactory)
    position = Sequence(lambda n: 'Position #{}'.format(n))
    # chassis_position == 'Numeric position' on the form
    chassis_position = Sequence(lambda n: n)
    remarks = Sequence(lambda n: 'Remarks #{}'.format(n))


class DeviceFactory(ParentDeviceFactory):
    name = Sequence(lambda n: 'Device #{}'.format(n))
    parent = SubFactory(ParentDeviceFactory)


class BulkeditTest(TestCase):
    """Tests bulk-edit form. Scenario:
        1. Edit single device, check the results and history changes.
        2. Edit two devices and check the results.
        3. Send form without marking fields being edited.
        4. Send form without save comment (i.e. description of your changes).
        5. Try to bulk-edit two devices while one of them is 'verified'.
        6. Try to bulk-edit two devices while both of them are 'verified'.
    """
    def setUp(self):
        self.client = login_as_su()
        self.device1 = DeviceFactory()
        self.device2 = DeviceFactory()

    def test_edit_single_device_and_check_history(self):
        url = '/ui/search/bulkedit/?'
        changed_fields = ['name', 'position', 'chassis_position', 'remarks']
        post_data = {
            'select': [self.device1.id],
            'edit': changed_fields,
            'name': 'new name',
            'position': 'VI',
            'chassis_position': 6,
            'remarks': 'some changed remark',
            'save_comment': 'some changed comment',
            'save': '',  # save form
        }
        self.client.post(url, post_data)
        device1 = Device.objects.get(id=self.device1.id)
        for field in changed_fields:
            self.assertEqual(getattr(device1, field), post_data[field])
        history = HistoryChange.objects.filter(device=self.device1)
        # 5 changes = 1 for device's creation + 4 for our changes
        self.assertEqual(history.count(), 5)
        comment = set([h.comment for h in history[1:]])
        # each one of our 4 changes should be recorded with the same comment
        self.assertEqual(len(comment), 1)
        self.assertEqual(comment.pop(), 'some changed comment')

    def test_edit_two_devices(self):
        url = '/ui/search/bulkedit/?'
        changed_fields = ['name', 'position', 'chassis_position', 'remarks']
        post_data = {
            'select': [self.device1.id, self.device2.id],
            'edit': changed_fields,
            'name': 'new name for both devices',
            'position': 'VI',
            'chassis_position': 6,
            'remarks': 'new remark for both devices',
            'save_comment': 'xxx',
            'save': '',  # save form
        }
        self.client.post(url, post_data)
        device1, device2 = Device.objects.filter(id__in=(self.device1.id,
                                                         self.device2.id))
        for field in changed_fields:
            self.assertEqual(getattr(device1, field), post_data[field])
            self.assertEqual(getattr(device1, field), getattr(device2, field))

    def test_send_form_without_marking_fields_being_edited(self):
        url = '/ui/search/bulkedit/?'
        post_data = {
            'select': [self.device1.id, self.device2.id],
            'edit': [],  # that should cause an error msg to appear
            'remarks': 'some remarks',
            'save': '',  # save form
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        err_msg = 'Please mark changed fields.'
        self.assertTrue(err_msg in response.content)

    def test_send_form_without_save_comment(self):
        url = '/ui/search/bulkedit/?'
        post_data = {
            'select': [self.device1.id, self.device2.id],
            'edit': ['remarks'],
            'remarks': 'some remarks without comment',
            'save_comment': '',
            'save': '',  # save form
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        err_msg = 'Please correct the errors.'
        self.assertTrue(err_msg in response.content)
        err_msg = 'You must describe your change'
        self.assertFormError(response, 'form', 'save_comment', err_msg)

    def test_two_devices_edit_one_verified(self):
        url = '/ui/search/bulkedit/?'
        changed_fields = ['name', 'position', 'chassis_position', 'remarks']
        post_data = {
            'select': [self.device1.id, self.device2.id],
            'edit': changed_fields,
            'name': 'new name for both devices',
            'position': 'VI',
            'chassis_position': 6,
            'remarks': 'new remark for both devices',
            'save_comment': 'xxx',
            'save': '',  # save form
        }
        self.device1.verified = True
        self.device1.save()
        self.client.post(url, post_data)
        device1, device2 = Device.objects.filter(id__in=(self.device1.id,
                                                         self.device2.id))
        # you shouldn't be able to bulk-edit devices marked as 'verified',
        # hence no changes will be saved for 'device1'
        for field in changed_fields:
            self.assertNotEqual(getattr(device1, field), post_data[field])
            self.assertEqual(getattr(device2, field), post_data[field])
            self.assertNotEqual(getattr(device1, field),
                                getattr(device2, field))

    def test_two_devices_edit_both_verified(self):
        url = '/ui/search/bulkedit/?'
        changed_fields = ['name', 'position', 'chassis_position', 'remarks']
        post_data = {
            'select': [self.device1.id, self.device2.id],
            'edit': changed_fields,
            'name': 'new name for both devices',
            'position': 'VI',
            'chassis_position': 6,
            'remarks': 'new remark for both devices',
            'save_comment': 'xxx',
            'save': '',  # save form
        }
        self.device1.verified = True
        self.device1.save()
        self.device2.verified = True
        self.device2.save()
        self.client.post(url, post_data)
        # both devices should remain unchanged
        device1, device2 = Device.objects.filter(id__in=(self.device1.id,
                                                         self.device2.id))
        for field in changed_fields:
            self.assertNotEqual(getattr(device1, field), post_data[field])
            self.assertNotEqual(getattr(device2, field), post_data[field])
            self.assertNotEqual(getattr(device1, field),
                                getattr(device2, field))
