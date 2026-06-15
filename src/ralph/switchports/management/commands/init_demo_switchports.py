import polars as pl

from django.core.management import BaseCommand

from ralph.assets.models import (
    Manufacturer,
    AssetModel,
    Category,
    ObjectModelType,
    Asset,
    Ethernet,
)
from ralph.data_center.models import DataCenterAsset
from ralph.switchports.backend import (
    NetmakerSwitchportBackend,
    SwitchDTO,
    InterfaceDTO,
)
from ralph.switchports.connections import connect
from ralph.switchports.models import Port
from ralph.virtual.models import CloudHost


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
        def _add_remote_asset(interface: InterfaceDTO) -> dict:
            dic = interface.model_dump(exclude={"vlans", "native_vlan", "mtu"})
            dic.update({"dca": self._get_remote_instance(interface)})
            return dic

        dry_run: bool = options["dry_run"]

        switches: list[str] = self.backend.get_switches()
        for switch_hostname in switches:
            switch: SwitchDTO = self.backend.get_switchports(switch_hostname)
            with pl.Config(tbl_rows=500, tbl_cols=30, fmt_str_lengths=100):
                print(
                    pl.DataFrame([_add_remote_asset(p) for p in reversed(switch.ports)])
                )

            if dry_run:
                continue

            switch_instance: DataCenterAsset = self._get_switch(switch)
            for interface_dto in switch.ports:
                port = Port.objects.get_or_create(
                    label=interface_dto.name, data_center_asset=switch_instance
                )[0]
                dca = self._get_remote_instance(interface_dto)
                if port and dca:
                    remote_port = Port.objects.get_or_create(
                        label=interface_dto.remote_port, data_center_asset=dca
                    )[0]
                    connect(port, remote_port)
                else:
                    print(
                        f"Could not connect port {interface_dto} to remote asset Port: {port}, DCA: {dca}"
                    )

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

    def _get_switch(self, switch: SwitchDTO) -> DataCenterAsset:
        return DataCenterAsset.objects.get(hostname=switch.hostname)

    def _get_remote_instance(self, interface: InterfaceDTO) -> DataCenterAsset | None:
        dca = self._get_remote_instance_by_mac(interface)
        if not dca:
            dca = self._get_remote_instance_by_hostname(interface)
        return dca

    def _get_remote_instance_by_mac(
        self, interface: InterfaceDTO
    ) -> DataCenterAsset | None:
        try:
            eth = Ethernet.objects.get(mac=interface.remote_id)
        except Ethernet.DoesNotExist:
            return None
        try:
            return Asset.polymorphic_objects.get(id=eth.base_object.id)
        except Asset.DoesNotExist:
            try:
                obj = CloudHost.objects.get(id=eth.base_object.id)
                return obj.hypervisor
            except CloudHost.DoesNotExist:
                return None

    def _get_remote_instance_by_hostname(
        self, interface: InterfaceDTO
    ) -> DataCenterAsset | None:
        hostname = self._get_hostname(interface)
        if not hostname:
            return None
        try:
            return Asset.polymorphic_objects.get(hostname=hostname)
        except Asset.DoesNotExist:
            try:
                obj = CloudHost.objects.get(hostname=hostname)
                return obj.hypervisor
            except CloudHost.DoesNotExist:
                return None

    def _get_hostname(self, interface: InterfaceDTO) -> str | None:
        def _get_from_remote_name():
            if len(interface.remote_name.split(" ")) > 1:
                return None
            if len(interface.remote_name.split(".")) < 2:
                return None
            return interface.remote_name

        def _get_from_desc():
            desc = interface.desc
            if len(desc.split()) >= 3 and len(desc.split()[0].split(".")) >= 2:
                return desc.split()[0]
            else:
                return None

        return _get_from_remote_name() or _get_from_desc()
