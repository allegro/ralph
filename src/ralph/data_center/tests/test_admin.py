from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection, transaction
from django.test import (
    override_settings,
    RequestFactory,
    TestCase,
    TransactionTestCase
)

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import (
    ServiceEnvironmentFactory,
    ServiceFactory
)
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.lib.custom_fields.models import (
    CustomField,
    CustomFieldTypes,
    CustomFieldValue
)


class DataCenterAssetAdminTestCaseMixin(object):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='root',
            password='password',
            email='email@email.pl'
        )
        result = self.client.login(username='root', password='password')
        self.assertEqual(result, True)
        self.factory = RequestFactory()
        self.dca = DataCenterAssetFactory(hostname='ralph1.allegro.pl')
        self.custom_fields_inline_prefix = 'custom_fields-customfieldvalue-content_type-object_id-'  # noqa

    def _update_dca(self, dca_data=None, inline_data=None):
        data = {
            'id': self.dca.id,
            'sn': self.dca.sn,
            'barcode': self.dca.barcode,
            'hostname': self.dca.hostname,
            'model': self.dca.model_id,
            'orientation': self.dca.orientation,
            'service_env': self.dca.service_env_id,
            'status': self.dca.status,
            'depreciation_rate': self.dca.depreciation_rate,
        }
        data.update(dca_data or {})
        if inline_data:
            data.update(self._prepare_inline_data(inline_data))
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(
            response.status_code,
            302,
            (
                repr(response.context['form'].errors)
                if response.context and 'form' in response.context else ''
            )
        )

    def _prepare_inline_data(self, d):
        return {
            '{}{}'.format(self.custom_fields_inline_prefix, k): v
            for (k, v) in d.items()
        }


class DataCenterAssetAdminMailNotificationsTestCase(
    DataCenterAssetAdminTestCaseMixin, TestCase
):
    def test_update_data_center_asset_check_mail_notifications(self):
        old_service = ServiceFactory(name='test')
        new_service = ServiceFactory(name='prod')
        old_service.business_owners.add(UserFactory(email='test1@test.pl'))
        new_service.business_owners.add(UserFactory(email='test2@test.pl'))
        old_service_env = ServiceEnvironmentFactory(service=old_service)
        new_service_env = ServiceEnvironmentFactory(service=new_service)
        # update without triggering signals
        DataCenterAsset.objects.filter(
            pk=self.dca.pk
        ).update(service_env=old_service_env)

        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 0,
        }
        self._update_dca(
            dca_data={'service_env': new_service_env.id},
            inline_data=data_custom_fields
        )

        self.dca.refresh_from_db()

        self.assertEqual(
            'Device has been assigned to Service: {} ({})'.format(
                new_service, self.dca
            ),
            mail.outbox[0].subject
        )
        self.assertCountEqual(
            mail.outbox[0].to,
            ['test1@test.pl', 'test2@test.pl']
        )


# TransactionTestCase has to be used here, since request to admin is wrapped
# in transaction (to test publishing dc host update data to hermes)
class DataCenterAssetAdminDCHostPublishUpdateTestCase(
    DataCenterAssetAdminTestCaseMixin, TransactionTestCase
):
    def setUp(self):
        super().setUp()
        self.custom_field_str = CustomField.objects.create(
            name='test_str', type=CustomFieldTypes.STRING, default_value='xyz'
        )
        self.custom_field_choices = CustomField.objects.create(
            name='test_choice', type=CustomFieldTypes.CHOICE,
            choices='qwerty|asdfgh|zxcvbn', default_value='zxcvbn',
            use_as_configuration_variable=True,
        )

    @override_settings(HERMES_HOST_UPDATE_TOPIC_NAME='ralph.host_update')
    @mock.patch('ralph.data_center.publishers.publish')
    def test_update_data_center_asset_check_publish_host_update(
        self, publish_mock
    ):
        self.cfv1 = CustomFieldValue.objects.create(
            object=self.dca,
            custom_field=self.custom_field_str,
            value='sample_value',
        )
        new_service = ServiceFactory(name='service1', uid='sc-44444')
        new_service_env = ServiceEnvironmentFactory(
            service=new_service, environment__name='dev'
        )

        data_custom_fields = {
            'TOTAL_FORMS': 3,
            'INITIAL_FORMS': 1,
            '0-id': self.cfv1.id,
            '0-custom_field': self.custom_field_str.id,
            '0-value': 'sample_value22',
            '1-id': '',
            '1-custom_field': self.custom_field_choices.id,
            '1-value': 'qwerty',
        }
        with transaction.atomic():
            self._update_dca(
                dca_data={
                    'service_env': new_service_env.id,
                    'hostname': 'my-host.mydc.net',
                },
                inline_data=data_custom_fields
            )
            # DCA is saved twice
            self.assertEqual(len(connection.run_on_commit), 2)

        self.dca.refresh_from_db()
        publish_data = publish_mock.call_args[0][1]
        publish_data.pop('modified')
        publish_data.pop('created')
        self.assertEqual(publish_data, {
            '__str__': 'data center asset: ' + str(self.dca),
            'configuration_path': None,
            'configuration_variables': {
                'test_choice': 'qwerty',
            },
            'custom_fields': {
                'test_str': 'sample_value22',
                'test_choice': 'qwerty'
            },
            'ethernet': [],
            'hostname': 'my-host.mydc.net',
            'id': self.dca.id,
            'ipaddresses': [],
            'object_type': 'datacenterasset',
            'parent': None,
            'remarks': '',
            'service_env': {
                'id': new_service_env.id,
                'service': 'service1',
                'environment': 'dev',
                'service_uid': 'sc-44444',
                'ui_url': ''
            },
            'tags': [],
            '_previous_state': {
                'hostname': 'ralph1.allegro.pl'
            },
        })
        # Despite `save` is called twice, publish update data is called only
        # once
        self.assertEqual(publish_mock.call_count, 1)
        # check if on_commit callbacks are removed from current db connections
        self.assertEqual(connection.run_on_commit, [])
