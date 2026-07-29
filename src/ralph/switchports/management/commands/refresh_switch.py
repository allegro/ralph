from django.core.management import BaseCommand

from ralph.switchports.netmaker.backend import (
    NetmakerSwitchportBackend,
)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = NetmakerSwitchportBackend()

    def add_arguments(self, parser):
        parser.add_argument(
            "--hostname",
            action="append",
            dest="hostnames",
            default=[],
            help="Hostname of switch to refresh. Repeatable.",
        )

    def handle(self, *args, **options):
        hostnames = options.get("hostnames", [])
        for hostname in hostnames:
            response = self.backend.refresh_switch(hostname)
            print(response)
