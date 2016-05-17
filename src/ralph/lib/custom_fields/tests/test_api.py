# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import SomeModel
from ..models import CustomField, CustomFieldTypes, CustomFieldValue


class CustomFieldsAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sm1 = SomeModel.objects.create(name='abc')
        cls.sm2 = SomeModel.objects.create(name='def')

        cls.custom_field_str = CustomField.objects.create(
            name='test_str', type=CustomFieldTypes.STRING, default_value='xyz'
        )
        cls.custom_field_choices = CustomField.objects.create(
            name='test_choice', type=CustomFieldTypes.CHOICE,
            choices='qwerty|asdfgh|zxcvbn', default_value='zxcvbn'
        )
        cls.cfv1 = CustomFieldValue.objects.create(
            object=cls.sm1,
            custom_field=cls.custom_field_str,
            value='sample_value',
        )
        cls.cfv2 = CustomFieldValue.objects.create(
            object=cls.sm2,
            custom_field=cls.custom_field_choices,
            value='qwerty',
        )

        cls.user = get_user_model().objects.create_superuser(
            username='root',
            password='password',
            email='email@email.pl'
        )
        cls.list_view_name = '{}-customfields-list'.format(
            SomeModel._meta.model_name
        )
        cls.detail_view_name = '{}-customfields-detail'.format(
            SomeModel._meta.model_name
        )

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_get_customfields_for_single_object(self):
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO: fix
        self.assertEqual(response.data['count'], 1)
        cfv = response.data['results'][0]
        self.assertEqual(
            cfv['custom_field']['name'], self.custom_field_str.name
        )
        self.assertEqual(cfv['value'], self.cfv1.value)
        self.assertTrue(cfv['url'].endswith(reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )))

    def test_get_customfields_for_single_object_options(self):
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        response = self.client.options(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('POST', response['allow'])

    def test_get_customfields_for_wrong_object_should_return_404(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.sm2.pk}
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_single_customfields_for_single_object(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['custom_field']['name'], self.custom_field_str.name
        )
        self.assertEqual(response.data['value'], self.cfv1.value)
        self.assertTrue(response.data['url'].endswith(reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )))

    def test_get_single_customfields_for_single_object_options(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        response = self.client.options(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('PUT', response['allow'])
        self.assertIn('PATCH', response['allow'])

    def test_add_new_customfield_value_should_pass(self):
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        data = {
            'value': 'qwerty',
            'custom_field': self.custom_field_choices.id,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cfv = CustomFieldValue.objects.get(pk=response.data['id'])
        self.assertEqual(cfv.object, self.sm1)
        self.assertEqual(cfv.custom_field, self.custom_field_choices)
        self.assertEqual(cfv.value, 'qwerty')

    def test_add_new_customfield_value_with_duplicated_customfield_should_not_pass(self):  # noqa
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        data = {
            'value': 'duplicate!',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        import ipdb; ipdb.set_trace()
