import ipaddress

from django.core.management import BaseCommand, CommandError
from django.db import transaction

from ralph.data_center.models import DataCenter
from ralph.dhcp.models import DNSServer, DNSServerGroup, DNSServerGroupOrder
from ralph.networks.models import IPAddress, Network, NetworkEnvironment


class Command(BaseCommand):
    """
    Generate a single, production ready network
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--dc-name',
            default='dc1',
            dest='dc_name',
            help='Data center name.'
        )
        parser.add_argument(
            '--dns1',
            default='10.0.0.11',
            dest='dns1',
            help='Primary DNS server.'
        )
        parser.add_argument(
            '--dns2',
            default='10.0.0.12',
            dest='dns2',
            help='Secondary DNS server.'
        )
        parser.add_argument(
            '--network-address',
            default='10.0.0.0',
            dest='network_address',
            help='Network address.'
        )
        parser.add_argument(
            '--network-mask',
            default='24',
            dest='network_mask',
            help='Network mask.'
        )
        parser.add_argument(
            '--gateway',
            default='10.0.0.1',
            dest='gateway',
            help='Default gateway.'
        )

    @classmethod
    @transaction.atomic
    def create_network(
        cls, network, dns1_address, dns2_address, gateway_address, dc_name
    ):
        dc = get_or_create(DataCenter, name=dc_name)
        network_environment = get_or_create(
            NetworkEnvironment, name='prod', data_center=dc
        )
        get_or_create(IPAddress, address=str(dns1_address))
        get_or_create(IPAddress, address=str(dns2_address))
        dns1 = get_or_create(DNSServer, ip_address=str(dns1_address))
        dns2 = get_or_create(DNSServer, ip_address=str(dns2_address))
        dns_server_group = get_or_create(
            DNSServerGroup, name='{}-dns-group'.format(dc_name),
        )
        dns_order = 10
        for dns in [dns1, dns2]:
            get_or_create(
                DNSServerGroupOrder, dns_server=dns,
                dns_server_group=dns_server_group, order=dns_order
            )
            dns_order += 10
        gateway_address = get_or_create(
            IPAddress, address=str(gateway_address)
        )
        get_or_create(
            Network,
            name=str(network),
            address=str(network),
            gateway=gateway_address,
            network_environment=network_environment,
            dns_servers_group=dns_server_group,
        )

    def handle(self, *args, **options):
        dc_name = options.get('dc_name')
        try:
            dns1_address = ipaddress.ip_address(options.get('dns1'))
            dns2_address = ipaddress.ip_address(options.get('dns2'))
            network_address = ipaddress.ip_address(
                options.get('network_address')
            )
            network = ipaddress.ip_network(
                '{}/{}'.format(
                    str(network_address),
                    options.get('network_mask')
                )
            )
            gateway_address = ipaddress.ip_address(options.get('gateway'))
        except ValueError as e:
            raise CommandError(e)

        self.create_network(
            network=network,
            dns1_address=dns1_address,
            dns2_address=dns2_address,
            gateway_address=gateway_address,
            dc_name=dc_name
        )


def get_or_create(model, **kwargs):
    obj, _ = model.objects.get_or_create(**kwargs)
    return obj
