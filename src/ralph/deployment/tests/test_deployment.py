from unittest import mock

from ddt import data, ddt, unpack
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import override_settings, TestCase

from ralph.assets.models import Ethernet
from ralph.assets.tests.factories import ServiceEnvironmentFactory
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.deployment.deployment import (
    autocomplete_service_env,
    check_ipaddress_unique
)
from ralph.networks.models.networks import IPAddress
from ralph.networks.tests.factories import (
    IPAddressFactory,
    NetworkEnvironmentFactory,
    NetworkFactory
)
from ralph.virtual.tests.factories import VirtualServerFactory


class _BaseTestDeploymentActionsTestCase(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._dns_record = {
            'pk': 10,
            'name': 's12345.mydc.net',
            'type': 1,
            'content': '10.20.30.40',
            'ptr': True,
            'owner': '_ralph'
        }

    def test_clean_hostname(self):
        self.instance.hostname = 'test'
        self.instance.__class__.clean_hostname([self.instance])
        # TODO: needs NullableCharField fix for VirtualServer
        # self.assertIsNone(self.instance.hostname)

    @override_settings(ENABLE_DNSAAS_INTEGRATION=True)
    @mock.patch('ralph.deployment.deployment.DNSaaS.get_dns_records')
    @mock.patch('ralph.deployment.deployment.DNSaaS.delete_dns_record')
    def test_clean_dns(self, delete_dns_record_mock, get_dns_records_mock):
        IPAddressFactory(address='10.20.30.41')
        IPAddressFactory(
            ethernet__base_object=self.instance, is_management=True
        )
        IPAddressFactory(
            ethernet__base_object=self.instance,
            ethernet__mac=None,
            ethernet__label=None,
            address='10.20.30.40',
        )
        delete_dns_record_mock.return_value = False
        get_dns_records_mock.return_value = [self._dns_record] * 3
        history = {self.instance.pk: {}}
        self.instance.__class__.clean_dns(
            [self.instance], history_kwargs=history
        )
        get_dns_records_mock.assert_called_with(['10.20.30.40'])
        self.assertEqual(delete_dns_record_mock.call_count, 3)
        delete_dns_record_mock.assert_called_with(10)

    @override_settings(ENABLE_DNSAAS_INTEGRATION=True)
    @mock.patch('ralph.deployment.deployment.DNSaaS.delete_dns_record')
    def test_clean_dns_with_no_ips(self, delete_dns_record_mock):
        IPAddressFactory(
            ethernet__base_object=self.instance, is_management=True
        )
        history = {self.instance.pk: {}}
        self.instance.__class__.clean_dns(
            [self.instance], history_kwargs=history
        )
        self.assertEqual(delete_dns_record_mock.call_count, 0)

    @override_settings(ENABLE_DNSAAS_INTEGRATION=True)
    @mock.patch('ralph.deployment.deployment.DNSaaS.get_dns_records')
    def test_clean_dns_with_too_much_ips(self, get_dns_records_mock):
        IPAddressFactory(
            ethernet__base_object=self.instance,
            ethernet__mac=None,
            ethernet__label=None,
            address='10.20.30.40',
        )
        history = {self.instance.pk: {}}
        get_dns_records_mock.return_value = [self._dns_record] * 50
        history = {self.instance.pk: {}}
        with self.assertRaises(Exception) as e:
            self.instance.__class__.clean_dns(
                [self.instance], history_kwargs=history
            )
        self.assertEqual(
            str(e.exception),
            'Cannot clean 50 entries for {} - clean it manually'.format(
                self.instance
            )
        )

    def test_clean_ipaddresses(self):
        ip = IPAddressFactory(ethernet__base_object=self.instance)
        ip_mgmt = IPAddressFactory(
            ethernet__base_object=self.instance, is_management=True
        )
        ip_without_eth = IPAddressFactory(
            ethernet__base_object=self.instance,
            ethernet__mac=None,
            ethernet__label=None,
        )
        self.instance.__class__.clean_ipaddresses([self.instance])
        # eth of ip should not be deleted
        ip.ethernet.refresh_from_db()
        # ip should be deleted
        with self.assertRaises(IPAddress.DoesNotExist):
            ip.refresh_from_db()
        # ip mgmt should not be deleted
        ip_mgmt.refresh_from_db()
        # ip without eth, as well as its ethernet should be deleted
        with self.assertRaises(Ethernet.DoesNotExist):
            ip_without_eth.ethernet.refresh_from_db()
        with self.assertRaises(IPAddress.DoesNotExist):
            ip_without_eth.refresh_from_db()

    def test_clean_dhcp(self):
        # TODO
        pass

    def _prepare_rack(self):
        self.rack = RackFactory()
        self.net_env = NetworkEnvironmentFactory(
            hostname_template_prefix='server_1',
            hostname_template_postfix='.mydc.net',
        )
        self.net = NetworkFactory(
            network_environment=self.net_env,
            address='10.20.30.0/24',
        )
        self.net.racks.add(self.rack)
        return self.net_env

    def test_assign_new_hostname(self):
        self._prepare_rack()
        next_free_hostname = self.instance.get_next_free_hostname()
        history = {self.instance.pk: {}}
        self.instance.__class__.assign_new_hostname(
            [self.instance], {'value': self.net_env.id}, history_kwargs=history
        )
        self.assertEqual(self.instance.hostname, next_free_hostname)
        self.assertEqual(history, {
            self.instance.pk: {
                'hostname': '{} (from {})'.format(
                    next_free_hostname, self.net_env
                )
            }
        })

    def test_assign_new_hostname_custom_value(self):
        self._prepare_rack()
        history = {self.instance.pk: {}}
        self.instance.__class__.assign_new_hostname(
            [self.instance],
            {'value': '__other__', '__other__': 's12345.mydc.net'},
            history_kwargs=history
        )
        self.assertEqual(self.instance.hostname, 's12345.mydc.net')
        self.assertEqual(history, {
            self.instance.pk: {'hostname': '{}'.format('s12345.mydc.net')}
        })

    def test_remove_entry_from_dhcp(self):
        history = {self.instance.pk: {}}
        ip = IPAddressFactory(
            address='10.20.30.40',
            hostname='s1234.mydc.net',
            ethernet__mac='aa:bb:cc:dd:ee:ff',
            ethernet__base_object=self.instance,
            dhcp_expose=True
        )
        self.instance.__class__.remove_from_dhcp_entries(
            [self.instance],
            ipaddress=ip.id,
            history_kwargs=history
        )
        ip.refresh_from_db()
        self.assertFalse(ip.dhcp_expose)
        self.assertEqual(history, {
            self.instance.pk: {
                'DHCP entry': '10.20.30.40 (s1234.mydc.net) / AA:BB:CC:DD:EE:FF'
            }
        })

    @override_settings(ENABLE_DNSAAS_INTEGRATION=True)
    @override_settings(DNSAAS_URL='https://dnsaas.mydc.net')
    @mock.patch('ralph.dns.dnsaas.DNSaaS._post')
    @mock.patch('ralph.dns.dnsaas.DNSaaS.get_domain')
    def test_create_dns_records(self, get_domain, _post):
        get_domain.return_value = 1
        history = {self.instance.pk: {'ip': '10.20.30.40'}}
        self.instance.hostname = 's12345.mydc.net'
        self.instance.__class__.create_dns_entries(
            [self.instance],
            history_kwargs=history
        )
        _post.assert_called_once_with(
            'https://dnsaas.mydc.net/api/v2/records/',
            {
                'type': 'A',
                'auto_ptr': settings.DNSAAS_AUTO_PTR_ALWAYS,
                'domain': 1,
                'name': 's12345.mydc.net',
                'content': '10.20.30.40',
                'owner': 'ralph'
            }
        )

    def test_check_ipaddress_unique_with_occupied_ip_should_raise_validation_error(self):  # noqa
        IPAddressFactory(address='10.20.30.40')
        with self.assertRaises(ValidationError):
            check_ipaddress_unique(
                [self.instance], {'ip_or_network': {
                    'value': '__other__', '__other__': '10.20.30.40'
                }}
            )

    def test_check_ipaddress_unique_with_ip_assigned_to_the_same_object_should_pass(self):
        IPAddressFactory(
            address='10.20.30.40', ethernet__base_object=self.instance
        )
        check_ipaddress_unique(
            [self.instance], {'ip_or_network': {
                'value': '__other__', '__other__': '10.20.30.40'
            }}
        )


class DataCenterAssetDeploymentActionsTestCase(
    _BaseTestDeploymentActionsTestCase, TestCase
):
    def setUp(self):
        self.instance = DataCenterAssetFactory()

    def _prepare_rack(self):
        super()._prepare_rack()
        self.instance.rack = self.rack
        self.instance.save()


class VirtualServerDeploymentActionsTestCase(
    _BaseTestDeploymentActionsTestCase, TestCase
):
    def setUp(self):
        self.instance = VirtualServerFactory()

    def _prepare_rack(self):
        super()._prepare_rack()
        self.instance.parent.rack = self.rack
        self.instance.parent.save()


@ddt
class AutocompleteFunctionsTestCase(TestCase):
    @unpack
    @data(
        ([],),
        ([DataCenterAssetFactory, DataCenterAssetFactory],)
    )
    def test_autocomplete_service_env_should_return_false(self, factories):
        self.assertFalse(
            autocomplete_service_env([], [factory() for factory in factories])
        )

    def test_autocomplete_service_env_should_return_pk(self):
        asset = DataCenterAssetFactory(service_env=ServiceEnvironmentFactory())
        self.assertEqual(
            asset.service_env.pk, autocomplete_service_env([], [asset])
        )
