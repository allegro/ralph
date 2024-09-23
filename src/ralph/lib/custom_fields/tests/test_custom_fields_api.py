# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase

from ..models import CustomField, CustomFieldTypes


class CustomFieldsAPITests(RalphAPITestCase):
    def setUp(self):
        self.custom_field_str = CustomField.objects.create(
            name='test str', type=CustomFieldTypes.STRING, default_value='xyz'
        )
        self.custom_field_choices = CustomField.objects.create(
            name='test choice', type=CustomFieldTypes.CHOICE,
            choices='qwerty|asdfgh|zxcvbn', default_value='zxcvbn',
            use_as_configuration_variable=True,
        )
        self.user = get_user_model().objects.create_superuser(
            username='root',
            password='password',
            email='email@email.pl'
        )
        self.client.force_authenticate(self.user)

    def test_get_custom_fields_list(self):
        url = reverse('customfield-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_custom_field_details(self):
        url = reverse(
            'customfield-detail', args=(self.custom_field_choices.id,)
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': 'test choice',
            'attribute_name': 'test_choice',
            'choices': ['qwerty', 'asdfgh', 'zxcvbn'],
            'use_as_configuration_variable': True,
            'default_value': 'zxcvbn',
            'url': self.get_full_url(url),
            'type': CustomFieldTypes.CHOICE.desc,
            'ui_url': self.get_full_url(
                self.custom_field_choices.get_absolute_url()
            ),
        })

    def test_create_custom_field(self):
        url = reverse('customfield-list')
        data = {
            'name': 'test choice 2',
            'type': 'choice list',
            'choices': ['1111', '222', '333'],
            'use_as_configuration_variable': True,
            'default_value': '333'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cf = CustomField.objects.get(name='test choice 2')
        self.assertEqual(cf._get_choices(), ['1111', '222', '333'])
        self.assertEqual(cf.default_value, '333')
        self.assertEqual(cf.use_as_configuration_variable, True)

    def test_update_custom_field(self):
        url = reverse(
            'customfield-detail', args=(self.custom_field_choices.id,)
        )
        data = {
            'name': 'new name for choices',
            'choices': ['9999', 'aaaa', 'xxx'],
            'default_value': 'aaaa'
        }
        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.custom_field_choices.refresh_from_db()
        self.assertEqual(
            self.custom_field_choices._get_choices(), ['9999', 'aaaa', 'xxx']
        )
        self.assertEqual(self.custom_field_choices.default_value, 'aaaa')
        self.assertEqual(self.custom_field_choices.name, 'new name for choices')
