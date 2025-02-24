# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ralph.accounts.models import RalphUser
from ralph.accounts.tests.factories import GroupFactory
from ralph.tests.factories import UserFactory

from ..models import CustomField, CustomFieldTypes, CustomFieldValue
from ..signals import api_post_create, api_post_update
from .models import ModelA, ModelB, SomeModel


class CustomFieldsAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.a1 = ModelA.objects.create()
        cls.b1 = ModelB.objects.create(a=cls.a1)
        cls.sm1 = SomeModel.objects.create(name='abc', b=cls.b1)
        cls.sm2 = SomeModel.objects.create(name='def')

        cls.custom_field_str = CustomField.objects.create(
            name='test str', type=CustomFieldTypes.STRING, default_value='xyz'
        )
        cls.custom_field_choices = CustomField.objects.create(
            name='test choice', type=CustomFieldTypes.CHOICE,
            choices='qwerty|asdfgh|zxcvbn', default_value='zxcvbn',
            use_as_configuration_variable=True,
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
        self.cfv1 = CustomFieldValue.objects.create(
            object=self.sm1,
            custom_field=self.custom_field_str,
            value='sample_value',
        )
        self.cfv2 = CustomFieldValue.objects.create(
            object=self.sm2,
            custom_field=self.custom_field_choices,
            value='qwerty',
        )
        self.cfv3 = CustomFieldValue.objects.create(
            object=self.sm2,
            custom_field=self.custom_field_str,
            value='sample_value2',
        )

    def test_get_customfields_in_object_resource(self):
        url = reverse('somemodel-detail', args=(self.sm2.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['custom_fields'], {
            'test_str': 'sample_value2',
            'test_choice': 'qwerty',
        })

    def test_get_customfields_with_inheritance_in_objects_list(self):
        CustomFieldValue.objects.create(
            object=self.a1,
            custom_field=self.custom_field_choices,
            value='asdfgh',
        )
        CustomFieldValue.objects.create(
            object=self.b1,
            custom_field=self.custom_field_str,
            value='sample_value_b1',
        )

        url = reverse('somemodel-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        cfvs = [obj['custom_fields'] for obj in response.data['results']]
        self.assertCountEqual(cfvs, [
            {
                'test_str': 'sample_value',
                'test_choice': 'asdfgh',
            },
            {
                'test_str': 'sample_value2',
                'test_choice': 'qwerty',
            }
        ])

    def test_get_customfields_with_inheritance_in_object_resource(self):
        CustomFieldValue.objects.create(
            object=self.a1,
            custom_field=self.custom_field_choices,
            value='asdfgh',
        )
        CustomFieldValue.objects.create(
            object=self.b1,
            custom_field=self.custom_field_str,
            value='sample_value_b1',
        )

        url = reverse('somemodel-detail', args=(self.sm1.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['custom_fields'], {
            'test_str': 'sample_value',
            'test_choice': 'asdfgh',
        })

    def test_get_configuration_variables_in_object_resource(self):
        url = reverse('somemodel-detail', args=(self.sm2.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['configuration_variables'], {
            'test_choice': 'qwerty',
        })

    def test_get_customfields_for_single_object(self):
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

    def test_get_customfields_with_inheritance_for_single_object(self):
        CustomFieldValue.objects.create(
            object=self.a1,
            custom_field=self.custom_field_choices,
            value='qwerty',
        )
        self.assertEqual(self.sm1.custom_fields.count(), 2)
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # besides that value of another CF is inherited, CFV assigned directly
        # to this object is only one and this only one should be editable
        # in context of this object
        self.assertEqual(response.data['count'], 1)

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

    def test_add_new_customfield_value_with_unmatching_managing_group_should_fail(self):  # noqa" E501

        self.custom_field_str.managing_group = GroupFactory()
        self.custom_field_str.save()

        some_object = SomeModel.objects.create(name='DEADBEEF')

        url = reverse(self.list_view_name, args=(some_object.id,))
        data = {
            'value': 'qwerty',
            'custom_field': self.custom_field_str.id,
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_new_customfield_value_with_matching_managing_group_should_succeed(self):  # noqa" E501
        group = GroupFactory()
        self.user.groups.add(group)
        self.custom_field_str.managing_group = group

        self.custom_field_str.save()
        self.user.save()

        some_object = SomeModel.objects.create(name='DEADBEEF')

        url = reverse(self.list_view_name, args=(some_object.id,))
        data = {
            'value': 'qwerty',
            'custom_field': self.custom_field_str.id,
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_customfield_value_with_unmatching_managing_group_should_fail(self):  # noqa: E501
        self.custom_field_str.managing_group = GroupFactory()
        self.custom_field_str.save()

        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        data = {
            'value': 'NEW-VALUE',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_customfield_value_with_matching_managing_group_should_pass(self):  # noqa: E501
        group = GroupFactory()
        self.user.groups.add(group)
        self.custom_field_str.managing_group = group

        self.custom_field_str.save()
        self.user.save()

        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        data = {
            'value': 'NEW-VALUE',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cfv1.refresh_from_db()
        self.assertEqual(self.cfv1.object, self.sm1)
        self.assertEqual(self.cfv1.custom_field, self.custom_field_str)
        self.assertEqual(self.cfv1.value, 'NEW-VALUE')


    def test_delete_custom_field_value_with_unmatching_managing_group_should_fail(self):  # noqa: E501
        self.custom_field_str.managing_group = GroupFactory()
        self.custom_field_str.save()

        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            CustomFieldValue.objects.filter(pk=self.cfv1.pk).count(), 1
        )

    def test_delete_custom_field_value_with_matching_managing_group_should_pass(self):  # noqa: E501
        group = GroupFactory()
        self.user.groups.add(group)
        self.custom_field_str.managing_group = group

        self.custom_field_str.save()
        self.user.save()

        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            CustomFieldValue.objects.filter(pk=self.cfv1.pk).count(), 0
        )

    def test_add_new_customfield_value_should_send_api_post_create_signal(self):  # noqa: E501
        self._sig_called_with_instance = None

        def listener(sender, instance, **kwargs):
            self._sig_called_with_instance = instance

        api_post_create.connect(listener)

        url = reverse(self.list_view_name, args=(self.sm1.id,))
        data = {
            'value': 'qwerty',
            'custom_field': self.custom_field_choices.id,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(self._sig_called_with_instance)
        self.assertEqual(
            self._sig_called_with_instance.id, response.data['id']
        )

    def test_add_new_customfield_value_by_attribute_name(self):
        expected = 'new-value'
        cf = CustomField.objects.create(
            name='by-attr', type=CustomFieldTypes.STRING, default_value='v'
        )
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        data = {
            'custom_field': cf.attribute_name,
            'value': expected,
        }

        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cfv = CustomFieldValue.objects.get(pk=response.data['id'])
        self.assertEqual(cfv.value, expected)

    def test_add_new_customfield_value_with_duplicated_customfield_should_not_pass(self):  # noqa
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        data = {
            'value': 'duplicate!',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Custom field of the same type already exists for this object.',
            response.data['__all__']
        )

    def test_add_new_customfield_value_with_invalid_value_should_not_pass(self):
        url = reverse(self.list_view_name, args=(self.sm1.id,))
        data = {
            'value': 'invalid!',
            'custom_field': self.custom_field_choices.id,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Select a valid choice. invalid! is not one of the available choices.',  # noqa
            response.data['__all__']
        )

    def test_update_customfield_value_should_pass(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        data = {
            'value': 'ytrewq',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cfv1.refresh_from_db()
        self.assertEqual(self.cfv1.object, self.sm1)
        self.assertEqual(self.cfv1.custom_field, self.custom_field_str)
        self.assertEqual(self.cfv1.value, 'ytrewq')

    def test_update_customfield_value_should_send_api_post_update_signal(self):
        self._sig_called_with_instance = None

        def listener(sender, instance, **kwargs):
            self._sig_called_with_instance = instance

        api_post_update.connect(listener)

        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        data = {
            'value': 'abc',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(self._sig_called_with_instance)
        self.assertEqual(
            self._sig_called_with_instance.id, response.data['id']
        )

    def test_update_customfield_value_with_duplicated_customfield_should_not_pass(self):  # noqa
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv2.pk, 'object_pk': self.cfv2.object_id}
        )
        data = {
            'value': 'duplicate!',
            'custom_field': self.custom_field_str.id,
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Custom field of the same type already exists for this object.',
            response.data['__all__']
        )

    def test_update_customfield_value_invalid_value_should_not_pass(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv2.pk, 'object_pk': self.cfv2.object_id}
        )
        data = {
            'value': 'invalid!',
            'custom_field': self.custom_field_choices.id,
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Select a valid choice. invalid! is not one of the available choices.',  # noqa
            response.data['__all__']
        )

    def test_partial_update_value_should_pass(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        data = {
            'value': 'ytrewq',
        }
        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cfv1.refresh_from_db()
        self.assertEqual(self.cfv1.object, self.sm1)
        self.assertEqual(self.cfv1.custom_field, self.custom_field_str)
        self.assertEqual(self.cfv1.value, 'ytrewq')

    def test_delete_custom_field_value(self):
        url = reverse(
            self.detail_view_name,
            kwargs={'pk': self.cfv1.pk, 'object_pk': self.cfv1.object_id}
        )
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            CustomFieldValue.objects.filter(pk=self.cfv1.pk).count(), 0
        )

    def test_filter_by_custom_field(self):
        url = '{}?{}'.format(
            reverse('{}-list'.format(SomeModel._meta.model_name)),
            'customfield__test_str=sample_value'
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
