# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import RequestFactory

from ralph.assets.models import Ethernet
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.networks.forms import validate_is_management
from ralph.networks.models import IPAddress
from ralph.networks.tests.factories import IPAddressFactory
from ralph.tests import RalphTestCase


class EmptyForm:
    cleaned_data = None


class NetworkLineFormsetTest(RalphTestCase):

    def test_validate_one_management(self):
        form_1 = EmptyForm()
        form_1.cleaned_data = {
            'DELETE': False,
            'is_management': True,
        }
        form_2 = EmptyForm()
        form_2.cleaned_data = {
            'DELETE': False,
            'is_management': True,
        }
        with self.assertRaisesRegex(
            ValidationError,
            (
                'Only one managment IP address can be assigned '
                'to this asset'
            )
        ):
            validate_is_management([form_1, form_2])


class TestDataCenterAssetForm(RalphTestCase):
    def setUp(self):
        self.dca = DataCenterAssetFactory()
        self.dca1 = DataCenterAssetFactory()

        self.user = get_user_model().objects.create_superuser(
            username='root',
            password='password',
            email='email@email.pl'
        )
        result = self.client.login(username='root', password='password')
        self.assertEqual(result, True)
        self.factory = RequestFactory()

    def _get_initial_data(self, dca=None):
        dca = dca or self.dca
        data = {
            'barcode': dca.barcode,
            'depreciation_rate': 25,
            'hostname': dca.hostname,
            'model': dca.model.pk,
            'orientation': 1,
            'service_env': dca.service_env.pk,
            'sn': dca.sn,
            'status': 1,
            'custom_fields-customfieldvalue-content_type-object_id-INITIAL_FORMS': '0',
            'custom_fields-customfieldvalue-content_type-object_id-MAX_NUM_FORMS': '1000',
            'custom_fields-customfieldvalue-content_type-object_id-MIN_NUM_FORMS': '0',
            'custom_fields-customfieldvalue-content_type-object_id-TOTAL_FORMS': '3',
        }
        return data

    def test_enter_valid_mgmt_should_pass(self):
        data = self._get_initial_data()
        data.update({
            'management_ip': '10.20.30.40',
            'management_hostname': 'qwerty.mydc.net',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.dca.refresh_from_db()
        self.assertEqual(self.dca.management_ip, '10.20.30.40')
        self.assertEqual(self.dca.management_hostname, 'qwerty.mydc.net')

    def test_enter_duplicated_mgmt_ip_should_not_pass(self):
        IPAddressFactory(
            is_management=True, address='10.20.30.41',
            ethernet__base_object=self.dca1,
        )
        data = self._get_initial_data()
        data.update({
            'management_ip': '10.20.30.41',
            'management_hostname': 'qwerty.mydc.net',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.dca.refresh_from_db()
        self.assertIn(
            'Management IP is already assigned to',
            response.context['errors'][0]
        )

    def test_enter_duplicated_mgmt_hostname_should_not_pass(self):
        IPAddressFactory(
            is_management=True, address='10.20.30.41',
            hostname='qwerty.mydc.net',
            ethernet__base_object=self.dca1,
        )
        data = self._get_initial_data()
        data.update({
            'management_ip': '10.20.30.42',
            'management_hostname': 'qwerty.mydc.net',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Management hostname is already assigned to',
            response.context['errors'][0]
        )

    def test_reenter_mgmt_ip_should_pass(self):
        IPAddressFactory(
            is_management=True, address='10.20.30.41',
            ethernet__base_object=self.dca,  # mgmt ip assigned to the same obj
        )
        data = self._get_initial_data()
        data.update({
            'management_ip': '10.20.30.41',
            'management_hostname': 'qwerty.mydc.net',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.dca.refresh_from_db()
        self.assertEqual(self.dca.management_ip, '10.20.30.41')
        self.assertEqual(self.dca.management_hostname, 'qwerty.mydc.net')

    def test_change_mgmt_ip_should_pass(self):
        IPAddressFactory(
            is_management=True, address='10.20.30.41',
            ethernet__base_object=self.dca,
        )
        ip_count = IPAddress.objects.count()
        data = self._get_initial_data()
        data.update({
            'management_ip': '10.20.30.42',
            'management_hostname': 'qwerty22.mydc.net',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.dca.refresh_from_db()
        self.assertEqual(self.dca.management_ip, '10.20.30.42')
        self.assertEqual(self.dca.management_hostname, 'qwerty22.mydc.net')
        self.assertEqual(ip_count, IPAddress.objects.count())

    def test_clean_mgmt_hostname_should_pass(self):
        IPAddressFactory(
            is_management=True, address='10.20.30.41',
            ethernet__base_object=self.dca,
        )
        data = self._get_initial_data()
        data.update({
            'management_ip': '10.20.30.42',
            'management_hostname': '',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.dca.refresh_from_db()
        self.assertEqual(self.dca.management_ip, '10.20.30.42')
        self.assertEqual(self.dca.management_hostname, '')

    def test_clean_mgmt_ip_when_mgmt_hostname_is_not_empty_should_not_pass(self):  # noqa
        IPAddressFactory(
            is_management=True, address='10.20.30.41',
            ethernet__base_object=self.dca,
        )
        data = self._get_initial_data()
        data.update({
            'management_ip': '',
            'management_hostname': 'qwerty.mydc.net',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Management IP could not be empty when management hostname is passed',  # noqa
            response.context['errors'][0]
        )

    def test_delete_mgmt(self):
        ip = IPAddressFactory(
            is_management=True, address='10.20.30.41',
            hostname='qwerty.mydc.net',
            ethernet__base_object=self.dca,
        )
        eth = ip.ethernet
        ip_count = IPAddress.objects.count()
        data = self._get_initial_data()
        data.update({
            'management_ip': '',
            'management_hostname': '',
        })
        response = self.client.post(self.dca.get_absolute_url(), data)
        self.assertEqual(response.status_code, 302)
        self.dca.refresh_from_db()
        self.assertEqual(self.dca.management_ip, '')
        self.assertEqual(self.dca.management_hostname, '')
        self.assertEqual(IPAddress.objects.count(), ip_count - 1)
        self.assertEqual(len(IPAddress.objects.filter(pk=ip.pk)), 0)
        self.assertEqual(len(Ethernet.objects.filter(pk=eth.pk)), 0)

    def test_create_new_data_center_asset_with_management(self):
        data = self._get_initial_data()
        data.update({
            'barcode': '1234',
            'sn': '321',
            'management_ip': '10.20.30.44',
            'management_hostname': 'qwerty.mydc.net',
        })
        response = self.client.post(
            reverse('admin:data_center_datacenterasset_add'), data
        )
        self.assertEqual(response.status_code, 302)
        dca = DataCenterAsset.objects.get(barcode='1234')
        self.assertEqual(dca.management_ip, '10.20.30.44')
        self.assertEqual(dca.management_hostname, 'qwerty.mydc.net')

    def test_create_new_data_center_asset_without_management(self):
        data = self._get_initial_data()
        data.update({
            'barcode': '1234',
            'sn': '321',
            'management_ip': '',
            'management_hostname': '',
        })
        ip_count = IPAddress.objects.count()
        response = self.client.post(
            reverse('admin:data_center_datacenterasset_add'), data
        )
        self.assertEqual(response.status_code, 302)
        dca = DataCenterAsset.objects.get(barcode='1234')
        self.assertEqual(dca.management_ip, '')
        self.assertEqual(dca.management_hostname, '')
        self.assertEqual(IPAddress.objects.count(), ip_count)

    def test_get_add_form(self):
        response = self.client.get(
            reverse('admin:data_center_datacenterasset_add'),
        )
        self.assertEqual(response.status_code, 200)

    def test_get_add_details_form(self):
        response = self.client.get(self.dca.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_get_add_details_form_with_management_ip(self):
        self.dca.management_ip = '10.20.30.40'
        self.dca.management_hostname = 'qwerty.mydc.net'
        response = self.client.get(self.dca.get_absolute_url())
        self.assertEqual(response.status_code, 200)
