import ipaddress

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command, CommandError
from django.db import transaction

from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.models import ConfigurationClass, ConfigurationModule
from ralph.data_importer.management.commands.create_network import \
    Command as NetworkCommand
from ralph.data_importer.management.commands.create_server_model import \
    Command as ServerModelCommand
from ralph.data_importer.management.commands.create_transitions import \
    Command as TransitionsCommand


class Command(BaseCommand):
    """
    Generate data useful to start a fresh and empty Ralph instance.
    """

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            parent_network = ipaddress.ip_network(options.get("parent_network"))
            dc_name = options.get("dc_name")
            server_room_name = options.get("server_room_name")
            network_address = parent_network.network_address
            dns_1 = ipaddress.ip_address(options.get("dns_1"))
            dns_2 = ipaddress.ip_address(options.get("dns_2"))
            number_of_subnets = int(options.get("number_of_subnets"))
            region = options.get("region")
            configuration_path = options.get("configuration_path")
        except ValueError as e:
            raise CommandError(e)

        self._validate_network(parent_network, number_of_subnets)
        self._validate_configuration_path(configuration_path)

        self.create_users(region)
        self.create_configuration_path(configuration_path)
        TransitionsCommand.create_data_center_asset_transitions()

        NetworkCommand.create_network(
            dc_name=dc_name,
            dns1_address=dns_1,
            dns2_address=dns_2,
            gateway_address=network_address + 1,
            network=parent_network,
            server_room_name=server_room_name,
        )
        for _ in range(0, number_of_subnets):
            network = ipaddress.ip_network("{}/{}".format(network_address, 24))
            NetworkCommand.create_network(
                dc_name=dc_name,
                dns1_address=dns_1,
                dns2_address=dns_2,
                gateway_address=network_address + 1,
                network=network,
                server_room_name=server_room_name,
                create_rack=True,
            )
            network_address += 256

        for name in ["A", "B", "C"]:
            ServerModelCommand.create_model(model_name="Model {}".format(name))
            ServerModelCommand.create_model(
                model_name="Blade server model {}".format(name), is_blade=True
            )

        call_command("sitetree_resync_apps")

    def add_arguments(self, parser):
        parser.add_argument(
            "-d", "--dc-name", default="dc1", dest="dc_name", help="Data center name."
        )
        parser.add_argument(
            "-s",
            "--server-room-name",
            default="server room",
            dest="server_room_name",
            help="Server room name.",
        )
        parser.add_argument(
            "-p",
            "--parent-network",
            default="10.0.0.0/16",
            dest="parent_network",
            help="Parent network address.",
        )
        parser.add_argument(
            "--dns1", default="10.0.0.11", dest="dns_1", help="Primary DNS server."
        )
        parser.add_argument(
            "--dns2", default="10.0.0.12", dest="dns_2", help="Secondary DNS server."
        )
        parser.add_argument(
            "-n",
            "--number-of-subnets",
            default="3",
            dest="number_of_subnets",
            help="Number of /24 subnets to be generated.",
        )
        parser.add_argument(
            "-r",
            "--region",
            default="PL",
            dest="region",
            help="Geographical region (eg. your location).",
        )
        parser.add_argument(
            "-c",
            "--configuration-path",
            default="configuration_module/default",
            dest="configuration_path",
            help="Default configuration path.",
        )

    def _validate_network(self, network, number_of_subnets):
        num_addresses = number_of_subnets * 256
        if network.num_addresses < num_addresses:
            raise CommandError(
                "Network {} will not accommodate {} /24 subnets.".format(
                    network, number_of_subnets
                )
            )
        max_netmask = ipaddress.ip_address("255.255.254.0")
        if network.netmask > max_netmask:
            raise CommandError("Net mask must be /23 or less.")

    def _validate_configuration_path(self, configuration_path):
        if len(configuration_path.split("/")) != 2:
            raise CommandError(
                "Configuration path must be a string with no spaces including"
                "one slash."
            )

    def create_users(self, region):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username="admin", is_staff=True, is_superuser=True
        )
        user.regions.add(RegionFactory(name=region))
        user.set_password("admin")
        user.save()

    def create_configuration_path(self, configuration_path):
        configuration_module, configuration_class = configuration_path.split("/")
        module = ConfigurationModule.objects.create(name=configuration_module)
        ConfigurationClass.objects.create(class_name=configuration_class, module=module)
