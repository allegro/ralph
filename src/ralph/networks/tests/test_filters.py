from unittest import mock 

from django.contrib.admin.options import IncorrectLookupParameters
from django.test import override_settings, RequestFactory, TestCase
from django.test.client import RequestFactory

from ralph.networks.admin import NetworkAdmin
from ralph.networks.filters import ContainsIPAddressFilter
from ralph.networks.models import Network
from ralph.networks.tests.factories import IPAddressFactory, NetworkFactory


class NetworkFiltersTestCase(TestCase):

    def setUp(self):
        super(NetworkFiltersTestCase, self).setUp()

        self.networks = (
            NetworkFactory(address='10.42.42.0/24'),
            NetworkFactory(address='10.42.0.0/16'),
            NetworkFactory(address='10.42.42.42/32'),
            NetworkFactory(address='10.43.42.0/24'),
        )

    def get_member_ip_filter(self, member_ip):
        return ContainsIPAddressFilter(
            field=Network._meta.get_field('max_ip'),
            request=None,
            params={'max_ip': member_ip},
            model=Network,
            model_admin=NetworkAdmin,
            field_path='max_ip'
        )

    def test_filter_member_ip_single_result(self):
        member_ip = '10.43.42.10'
        expected_network = '10.43.42.0/24'

        member_ip_filter = self.get_member_ip_filter(member_ip)
        queryset = member_ip_filter.queryset(None, Network.objects.all())

        results = [str(net.address) for net in queryset.all()]

        self.assertEqual(1, len(results))
        self.assertEqual(expected_network, results.pop())

    def test_filter_member_ip_range_overlap(self):
        member_ip = '10.42.42.10'
        expected_networks = ['10.42.0.0/16', '10.42.42.0/24']

        member_ip_filter = self.get_member_ip_filter(member_ip)
        queryset = member_ip_filter.queryset(None, Network.objects.all())

        results = [str(net.address) for net in queryset.all()]
        results.sort()

        self.assertEqual(2, len(results))
        self.assertEqual(expected_networks, results)
        
    def test_filter_member_ip_no_results(self):
        member_ip = '10.10.10.10'

        member_ip_filter = self.get_member_ip_filter(member_ip)
        queryset = member_ip_filter.queryset(None, Network.objects.all())

        results = [str(net.address) for net in queryset.all()]

        self.assertEqual([], results)

    def test_filter_member_ip_empty_value(self):
        member_ip = ''

        member_ip_filter = self.get_member_ip_filter(member_ip)
        queryset = member_ip_filter.queryset(None, Network.objects.all())

        results = [str(net.address) for net in queryset.all()]

        self.assertEqual(4, len(results))

    def test_filter_member_invalid_input_raises_correct_valudation_error(self):
        member_ip = 'DEADBEEF'

        rf = RequestFactory()
        fake_request = rf.get('/')

        # NOTE(romcheg): Need to attach _messages property to the fake request
        #                in order to make it compatible with MessageMiddleware.
        fake_request._messages = mock.Mock()


        member_ip_filter = self.get_member_ip_filter(member_ip)

        with self.assertRaises(IncorrectLookupParameters):
            queryset = member_ip_filter.queryset(
                fake_request,
                Network.objects.all()
            )
