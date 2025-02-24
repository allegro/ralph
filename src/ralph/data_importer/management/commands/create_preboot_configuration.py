from django.core.management import BaseCommand
from django.db import transaction

from ralph.deployment.models import (
    Preboot,
    PrebootConfiguration,
    PrebootItemType
)


class Command(BaseCommand):
    """
    Generate a production ready preboot configuration.
    """

    @transaction.atomic
    def handle(self, *args, **options):
        kickstart_file = options.get("kickstart_file")
        ipxe_file = options.get("ipxe_file")
        description = options.get("description")
        if kickstart_file:
            with open(kickstart_file, "r") as file:
                kickstart_file_data = file.read()
        else:
            kickstart_file_data = ""
        if ipxe_file:
            with open(ipxe_file, "r") as file:
                ipxe_file_data = file.read()
        else:
            ipxe_file_data = ""
        preboot_name = options.get("preboot_name")
        self.create_preboot_configuration(
            kickstart_file_data, ipxe_file_data, preboot_name, description
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "-k",
            "--kickstart-file",
            default=None,
            dest="kickstart_file",
            help="Path to a file with kickstart content.",
        )
        parser.add_argument(
            "-i",
            "--ipxe-file",
            default=None,
            dest="ipxe_file",
            help="Path to a file with ipxe content.",
        )
        parser.add_argument(
            "-d",
            "--description",
            default="Automatically generated preboot.",
            dest="description",
            help="Preboot description.",
        )
        parser.add_argument(
            "-n",
            "--preboot-configuration-name",
            default="Preboot",
            dest="preboot_name",
            help="Preboot configuration name.",
        )

    @classmethod
    def create_preboot_configuration(
        cls, kickstart_file, ipxe_file, preboot_name, description
    ):
        kickstart_file, _ = PrebootConfiguration.objects.get_or_create(
            name="{} kickstart".format(preboot_name),
            type=PrebootItemType.kickstart.id,
            configuration=kickstart_file,
        )
        ipxe_file, _ = PrebootConfiguration.objects.get_or_create(
            name="{} ipxe".format(preboot_name),
            type=PrebootItemType.ipxe.id,
            configuration=ipxe_file,
        )
        preboot, _ = Preboot.objects.get_or_create(
            name=preboot_name, description=description
        )
        preboot.items.add(ipxe_file)
        preboot.items.add(kickstart_file)
