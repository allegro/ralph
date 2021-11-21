import ipaddress

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command, CommandError
from django.db import transaction

from ralph.accounts.tests.factories import RegionFactory
from ralph.data_importer.management.commands.create_network import \
    Command as NetworkCommand
from ralph.data_importer.management.commands.create_network import get_or_create
from ralph.data_importer.management.commands.create_transitions import \
    Command as TransitionsCommand


class Command(BaseCommand):
    """
    Generate data useful to start a fresh and empty Ralph instance.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--dc-name',
            default='dc1',
            dest='dc_name',
            help='Data center name.'
        )
        parser.add_argument(
            '-n', '--parent-network',
            default='10.0.0.0/16',
            dest='parent_network',
            help='Parent network address.'
        )
        parser.add_argument(
            '--dns1',
            default='10.0.0.11',
            dest='dns_1',
            help='Primary DNS server.'
        )
        parser.add_argument(
            '--dns2',
            default='10.0.0.12',
            dest='dns_2',
            help='Secondary DNS server.'
        )
        parser.add_argument(
            '-s', '--number-of-subnets',
            default='3',
            dest='number_of_subnets',
            help='Number of /24 subnets to be generated.'
        )
        parser.add_argument(
            '-r', '--region',
            default='PL',
            dest='region',
            help='Geographical region (eg. your location).'
        )

    def create_users(self, region):
        user_model = get_user_model()
        user = get_or_create(
            user_model, username='admin', is_staff=True, is_superuser=True
        )
        user.regions.add(RegionFactory(name=region))
        user.set_password('admin')
        user.save()

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            parent_network = ipaddress.ip_network(
                options.get('parent_network')
            )
            dc_name = options.get('dc_name')
            network_address = parent_network.network_address
            dns_1 = ipaddress.ip_address(options.get('dns_1'))
            dns_2 = ipaddress.ip_address(options.get('dns_2'))
            number_of_subnets = int(options.get('number_of_subnets'))
            region = options.get('region')
        except ValueError as e:
            raise CommandError(e)

        self._validate_network(parent_network, number_of_subnets)

        self.create_users(region)
        TransitionsCommand.create_data_center_asset_transitions()

        NetworkCommand.create_network(
            dc_name=dc_name,
            dns1_address=dns_1,
            dns2_address=dns_2,
            gateway_address=network_address + 1,
            network=parent_network
        )
        for _ in range(0, number_of_subnets):
            network = ipaddress.ip_network('{}/{}'.format(network_address, 24))
            NetworkCommand.create_network(
                dc_name=dc_name,
                dns1_address=dns_1,
                dns2_address=dns_2,
                gateway_address=network_address + 1,
                network=network
            )
            network_address += 256
        call_command('sitetree_resync_apps')

    def _validate_network(self, network, number_of_subnets):
        num_addresses = number_of_subnets * 256
        if network.num_addresses < num_addresses:
            raise CommandError(
                "Network {} will not accommodate {} /24 subnets.".format(
                    network, number_of_subnets
                )
            )
        max_netmask = ipaddress.ip_address('255.255.254.0')
        if network.netmask > max_netmask:
            raise CommandError(
                "Net mask must be /23 or less."
            )
