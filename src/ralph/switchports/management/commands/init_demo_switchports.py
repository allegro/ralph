from pprint import pp

from django.core.management import BaseCommand
from django.db import transaction

from ralph.assets.models import Manufacturer, AssetModel, Category, ObjectModelType
from ralph.data_center.models import DataCenterAsset, DataCenter, ServerRoom, Rack
from ralph.switchports.backend import (
    NetmakerSwitchportBackend,
    SwitchDTO,
    InterfaceDTO,
    InterfaceStatus,
    InterfaceMode,
)
from ralph.switchports.models import Port, Connection, ConnectionMember


class Command(BaseCommand):
    help = "Create Switches and SwitchPorts based on Netmaker data for demo purposes."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = NetmakerSwitchportBackend()
        self.unknown_model, _ = AssetModel.objects.get_or_create(
            name="UNKNOWN_MODEL", type=ObjectModelType.data_center
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't modify the database, just print what would be created.",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]

        switches: list[str] = self.backend.get_switches()
        for switch_hostname in switches:  # TODO
            switch: SwitchDTO = self.backend.get_switchports(switch_hostname)
            if dry_run:
                pp(switch)
                continue

            switch_instance: DataCenterAsset = self._get_or_create_switch(
                switch, include_rack=True
            )
            for interface_dto in switch.ports:
                port = self._get_or_create_port(
                    switch_instance,
                    interface_dto,
                    up_only=True,
                    access_only=True,
                    downlink_only=True,
                )
                self._create_related_asset_and_connection(
                    interface_dto, port
                ) if port else None

    def _get_or_create_model(self, switch: SwitchDTO) -> AssetModel:
        return AssetModel.objects.get_or_create(
            name=switch.model,
            manufacturer=self._get_or_create_manufacturer(switch),
            category=self._get_or_create_category(switch),
            type=ObjectModelType.data_center,
        )[0]

    def _get_or_create_category(self, switch: SwitchDTO) -> Category:
        return Category.objects.get_or_create(name="Switch Ethernet Rack")[0]

    def _get_or_create_manufacturer(self, switch: SwitchDTO) -> Manufacturer:
        return Manufacturer.objects.get_or_create(name=switch.manufacturer_name)[0]

    def _get_or_create_switch(
        self, switch: SwitchDTO, include_rack=True
    ) -> DataCenterAsset:
        rack = None
        if include_rack:
            dc, _ = DataCenter.objects.get_or_create(name=switch.location_dc)
            server_room, _ = ServerRoom.objects.get_or_create(
                name="UNKNOWN", data_center=dc
            )
            rack, _ = Rack.objects.get_or_create(
                name=switch.location_rack, defaults={"server_room": server_room}
            )

        dca, created = DataCenterAsset.objects.get_or_create(
            hostname=switch.hostname,
            defaults={
                "model": self._get_or_create_model(switch),
                "rack": rack if include_rack else None,
                "position": switch.location_position if include_rack else None,
                "barcode": switch.barcode,
                "sn": switch.sn,
            },
        )
        if created:
            self.stdout.write(f"Created switch {dca.hostname}")
        else:
            self.stdout.write(f"Switch {dca.hostname} already exists")
            self.stdout.write(f"Data: {switch.model_dump(exclude={'ports'})}")
        return dca

    def _get_or_create_port(
        self,
        switch: DataCenterAsset,
        port: InterfaceDTO,
        up_only=True,
        access_only=True,
        downlink_only=True,
    ) -> Port | None:
        if up_only and port.status != InterfaceStatus.UP:
            return None
        if access_only and port.interface_mode != InterfaceMode.ACCESS:
            return None
        if downlink_only and port.uplink:
            return None
        self.stdout.write(
            f"Will create port {port.model_dump(include={'name', 'status', 'interface_mode', 'remote_name', 'remote_port'})}"
        )  # 'name', 'status', 'interface_mode', 'remote_name', 'remote_port'})}" )  # include={'name', 'status', 'type'})}")
        return Port.objects.get_or_create(label=port.name, data_center_asset=switch)[0]

    def _create_related_asset_and_connection(
        self, interface: InterfaceDTO, switch_port: Port
    ) -> tuple[Port, Connection] | None:
        if not self._hostname_valid(interface.remote_name):
            return None
        dca, _ = (
            DataCenterAsset.objects.get_or_create(  # this will not always be a DCA in real life
                hostname=interface.remote_name, defaults={"model": self.unknown_model}
            )
        )
        host_port: Port = Port.objects.get_or_create(
            label=interface.remote_port, data_center_asset=dca
        )[0]

        connection_1 = Connection.objects.filter(members__port=switch_port).first()
        connection_2 = Connection.objects.filter(members__port=host_port).first()
        both_connections = bool(connection_1 and connection_2)
        if both_connections and connection_1 == connection_2:
            return host_port, connection_1

        with transaction.atomic():
            if both_connections:
                connection_1.delete()
                connection_2.delete()
            else:
                if connection_1:
                    connection_1.delete()
                if connection_2:
                    connection_2.delete()
            conn = Connection.objects.create()
            for port in [switch_port, host_port]:
                ConnectionMember.objects.get_or_create(connection=conn, port=port)

        return host_port, conn

    def _hostname_valid(self, hostname: str) -> bool:
        """Simple validation"""
        if len(hostname.split(" ")) > 1:
            return False
        if len(hostname.split(".")) < 2:
            return False
        return True
