# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ralph.util.models import (
    CustomAttribute,
    CustomAttributeOption,
    CustomAttributeStringValue,
    CustomAttributeTypes,
)
from ralph.util.tests.models import MyDevice

from ralph.discovery.models_device import Device


class CustomAttributeTest(TestCase):
    """Basic tests for custom attributes"""

    def setUp(self):
        self.device = MyDevice(name='Test device')
        self.device.save()
        self.ca1 = CustomAttribute(
            name='ca1',
            verbose_name='Custom Attribute 1',
            type=CustomAttributeTypes.STRING,
            content_type=ContentType.objects.get_for_model(MyDevice),
        )
        self.ca1.save()
        self.ca2 = CustomAttribute(
            name='ca2',
            verbose_name='Custom Attribute 2',
            type=CustomAttributeTypes.SINGLE_CHOICE,
            content_type=ContentType.objects.get_for_model(MyDevice)
        )
        self.ca2.save()
        self.opt1 = CustomAttributeOption(
            custom_attribute=self.ca2,
            value='Option 1',
        )
        self.opt1.save()
        self.opt2 = CustomAttributeOption(
            custom_attribute=self.ca2,
            value='Option 2',
        )
        self.opt2.save()
        self.opt3 = CustomAttributeOption(
            custom_attribute=self.ca2,
            value='Option 3',
        )
        self.opt3.save()

    def test_choice_value_can_be_set_by_value(self):
        self.device.ca2 = 'Option 1'
        self.device.save()
        device = MyDevice.objects.get(pk=self.device.pk)
        self.assertEqual(device.ca2.value, 'Option 1')

    def test_choice_value_raises_valueerror_when_nonexistent_option_used(self):
        with self.assertRaises(ValueError):
            self.device.ca2 = 'Option X'

    def test_value_is_none_if_unset(self):
        self.assertIsNone(self.device.ca2)

    def test_value_is_persistend_when_reloading_object(self):
        self.device.ca1 = 'Some string'
        self.device.save()
        device = MyDevice.objects.get(pk=self.device.pk)
        self.assertEqual(device.ca1, 'Some string')

    def test_value_can_be_set_when_object_already_exists(self):
        device = MyDevice.objects.get(pk=self.device.pk)
        device.ca1 = 'Some string 2'
        device.save()
        device = MyDevice.objects.get(pk=device.pk)
        self.assertEqual(device.ca1, 'Some string 2')

    def test_attribute_is_converted_to_str_as_verbose_name(self):
        self.assertEqual(unicode(self.ca1), self.ca1.verbose_name)

    def test_attribute_value_is_converted_to_str_as_simple_expression(self):
        self.device.ca1 = 'Some string' 
        self.device.save()
        custom_attr = CustomAttributeStringValue.objects.get(
            object_id=self.device.pk,
            content_type=ContentType.objects.get_for_model(MyDevice),
        )
        self.assertEqual(
            unicode(custom_attr),
            'Test device.Custom Attribute 1 = Some string')

    def test_attribute_value_can_be_set_when_already_set(self):
        self.device.ca1 = 'Some string' 
        self.device.save()
        self.device.ca1 = 'Some other string'
        self.device.save()
        device = MyDevice.objects.get(pk=self.device.pk)
        self.assertEqual(device.ca1, 'Some other string')
