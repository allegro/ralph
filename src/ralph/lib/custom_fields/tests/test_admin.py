from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from ralph.accounts.tests.factories import GroupFactory

from ..models import CustomField, CustomFieldTypes, CustomFieldValue
from .models import ModelA, ModelB, SomeModel


class CustomFieldValueAdminMaxinTestCase(TestCase):
    def setUp(self):
        self.inline_prefix = 'custom_fields-customfieldvalue-content_type-object_id-'  # noqa
        self.a1 = ModelA.objects.create()
        self.b1 = ModelB.objects.create(a=self.a1)
        self.sm1 = SomeModel.objects.create(name='abc', b=self.b1)
        self.sm2 = SomeModel.objects.create(name='def')

        self.custom_field_str = CustomField.objects.create(
            name='test_str', type=CustomFieldTypes.STRING, default_value='xyz'
        )
        self.custom_field_choices = CustomField.objects.create(
            name='test_choice', type=CustomFieldTypes.CHOICE,
            choices='qwerty|asdfgh|zxcvbn', default_value='zxcvbn'
        )
        self.cfv1 = CustomFieldValue.objects.create(
            object=self.sm1,
            custom_field=self.custom_field_str,
            value='sample_value',
        )

        self.user = get_user_model().objects.create_superuser(
            username='root',
            password='password',
            email='email@email.pl'
        )
        result = self.client.login(username='root', password='password')
        self.assertEqual(result, True)
        self.factory = RequestFactory()

    def _prepare_inline_data(self, d):
        return {
            '{}{}'.format(self.inline_prefix, k): v for (k, v) in d.items()
        }

    def test_get_customfield_formfield_for_choicefield(self):
        response = self.client.get(reverse(
            'admin:customfield_formfield',
            args=(self.custom_field_choices.id,)
        ))
        self.assertContains(response, '<select name="__empty__">')
        # default_value should be selected
        self.assertContains(
            response,
            '<option value="zxcvbn" selected>zxcvbn</option>'
        )

    def test_get_customfield_formfield_for_string_field(self):
        response = self.client.get(reverse(
            'admin:customfield_formfield',
            args=(self.custom_field_str.id,)
        ))
        # default_value should be placed
        self.assertContains(
            response,
            '<input type="text" name="__empty__" value="xyz">'
        )

    def test_add_new_custom_field_value_for_existing_object(self):
        data = {
            'id': self.sm1.id,
            'name': self.sm1.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            '1-custom_field': self.custom_field_choices.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        response = self.client.post(self.sm1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomFieldValue.objects.filter(
            object_id=self.sm1.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
        ).count(), 2)
        cfv = CustomFieldValue.objects.get(
            object_id=self.sm1.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
            custom_field=self.custom_field_choices,
        )
        self.assertEqual(cfv.value, 'qwerty')

    def test_add_new_custom_field_value_for_new_object(self):
        data = {
            'name': 'qwerty'
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 0,
            '0-id': '',
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            '1-custom_field': self.custom_field_choices.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        response = self.client.post(SomeModel.get_add_url(), data)
        self.assertEqual(response.status_code, 302)
        sm = SomeModel.objects.get(name='qwerty')
        self.assertEqual(CustomFieldValue.objects.filter(
            object_id=sm.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
        ).count(), 2)
        cfv_str = CustomFieldValue.objects.get(
            object_id=sm.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
            custom_field=self.custom_field_str,
        )
        self.assertEqual(cfv_str.value, 'sample_value')
        cfv_choices = CustomFieldValue.objects.get(
            object_id=sm.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
            custom_field=self.custom_field_choices,
        )
        self.assertEqual(cfv_choices.value, 'qwerty')

    def test_validate_choice_custom_field(self):
        data = {
            'id': self.sm1.id,
            'name': self.sm1.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            '1-custom_field': self.custom_field_choices.id,
            '1-value': 'qwerty11',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        response = self.client.post(self.sm1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Select a valid choice. qwerty11 is not one of the available choices',
            response.context_data['errors'][0][0],
        )

    def test_duplicate_custom_field_one_existing(self):
        data = {
            'id': self.sm1.id,
            'name': self.sm1.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            # duplicated value for custom_field_str
            '1-custom_field': self.custom_field_str.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        response = self.client.post(self.sm1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Custom field of the same type already exists for this object',
            response.context_data['errors'][0][0]
        )

    def test_duplicate_custom_field_both_new(self):
        data = {
            'id': self.sm2.id,
            'name': self.sm2.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 0,
            '0-id': '',
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            # duplicated value for custom_field_str
            '1-custom_field': self.custom_field_str.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        response = self.client.post(self.sm1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Custom field of the same type already exists for this object.',
            response.context_data['errors'][0][0],
        )

    def test_duplicate_custom_field_for_new_object(self):
        data = {
            'name': 'new_some_model',
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 0,
            '0-id': '',
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            # duplicated value for custom_field_str
            '1-custom_field': self.custom_field_str.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        response = self.client.post(SomeModel.get_add_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Please correct the duplicate data for custom fields (only one '
            'value for particular custom field is possible).',
            response.context_data['errors'],
        )

    def test_clearing_values_of_children_objects(self):
        data = {}
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 0,
            '0-id': '',
            '0-custom_field': self.custom_field_str.id,
            '0-clear_children': 'on',
            '0-value': 'sample_value333',
        }
        data.update(self._prepare_inline_data(data_custom_fields))
        self.assertIn(self.cfv1, list(self.sm1.custom_fields.all()))
        response = self.client.post(self.a1.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.cfv1, list(self.sm1.custom_fields.all()))

    def test_custom_field_not_in_form_for_nonmatching_managing_group(self):
        self.custom_field_str.managing_group = GroupFactory()
        self.custom_field_str.save()

        response = self.client.get(self.sm1.get_absolute_url())

        self.assertEqual(1, len(response.context_data['custom_fields_all']))
        self.assertEqual(
            'sample_value',
            response.context_data['custom_fields_all'][0]['value']
        )

        filled_in_custom_field_forms = [
            form
            for form in response.context_data['inline_admin_formsets'][0].formset.forms  # noqa: E501
            if form.fields['id'].initial is not None
        ]

        self.assertEqual(0, len(filled_in_custom_field_forms))


    def test_custom_field_in_form_for_matching_managing_group(self):
        group = GroupFactory()

        self.user.groups.add(group)
        self.custom_field_str.managing_group = group

        self.user.save()
        self.custom_field_str.save()

        response = self.client.get(self.sm1.get_absolute_url())

        self.assertEqual(1, len(response.context_data['custom_fields_all']))
        self.assertEqual(
            'sample_value',
            response.context_data['custom_fields_all'][0]['value']
        )

        filled_in_custom_field_forms = [
            form
            for form in response.context_data['inline_admin_formsets'][0].formset.forms  # noqa: E501
            if form.fields['id'].initial is not None
        ]

        self.assertEqual(1, len(filled_in_custom_field_forms))
        form = filled_in_custom_field_forms[0]

        self.assertEqual(
            self.cfv1.id,
            form.fields['id'].initial
        )

    def test_add_new_custom_field_value_succeeds_with_matching_managing_group(self):  # noqa: E501
        group = GroupFactory()

        self.user.groups.add(group)
        self.custom_field_choices.managing_group = group

        self.user.save()
        self.custom_field_choices.save()

        data = {
            'id': self.sm1.id,
            'name': self.sm1.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            '1-custom_field': self.custom_field_choices.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))

        response = self.client.post(
            self.sm1.get_absolute_url(),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        custom_field_qs = CustomFieldValue.objects.filter(
            object_id=self.sm1.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
            custom_field=self.custom_field_choices,
            value='qwerty'
        )
        self.assertTrue(custom_field_qs.exists())

    def test_add_new_custom_field_value_fails_with_nonmatching_managing_group(self):  # noqa: E501
        group = GroupFactory()

        self.custom_field_choices.managing_group = group
        self.custom_field_choices.save()

        data = {
            'id': self.sm1.id,
            'name': self.sm1.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value',
            '1-id': '',
            '1-custom_field': self.custom_field_choices.id,
            '1-value': 'qwerty',
        }
        data.update(self._prepare_inline_data(data_custom_fields))

        response = self.client.post(
            self.sm1.get_absolute_url(),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        expected_error_message = f'Only users from {group.name} group can set this custom field'
        self.assertIn('errors', response.context_data)
        self.assertIn(expected_error_message, response.context_data['errors'][0][0])

        custom_field_qs = CustomFieldValue.objects.filter(
            object_id=self.sm1.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
            custom_field=self.custom_field_choices,
            value='qwerty'
        )
        self.assertFalse(custom_field_qs.exists())

    def test_edit_custom_field_value_fails_with_nonmatching_managing_group(self):  # noqa: E501
        group = GroupFactory()

        self.custom_field_str.managing_group = group
        self.custom_field_str.save()

        data = {
            'id': self.sm1.id,
            'name': self.sm1.name,
        }
        data_custom_fields = {
            'TOTAL_FORMS': 2,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'NEW-VALUE',
        }
        data.update(self._prepare_inline_data(data_custom_fields))

        response = self.client.post(
            self.sm1.get_absolute_url(),
            data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        expected_error_message = f'Only users from {group.name} group can set this custom field'
        self.assertIn('errors', response.context_data)
        self.assertIn(expected_error_message, response.context_data['errors'][0][0])

        custom_field_qs = CustomFieldValue.objects.filter(
            object_id=self.sm1.id,
            content_type=ContentType.objects.get_for_model(SomeModel),
            custom_field=self.custom_field_str,
            value='sample_value'
        )
        self.assertTrue(custom_field_qs.exists())
