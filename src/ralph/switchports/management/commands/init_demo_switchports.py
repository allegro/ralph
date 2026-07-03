import itertools
from collections import Counter, defaultdict

import polars as pl
from django.core.management import BaseCommand

from ralph.assets.models import (
    AssetModel,
    Category,
    Manufacturer,
    ObjectModelType,
)
from ralph.data_center.models import DataCenterAsset
from ralph.switchports.asset_matching import RemoteAsset, cross_validate, extract_asset
from ralph.switchports.backend import (
    NetmakerSwitchportBackend,
    SwitchDTO,
)
from ralph.switchports.dto import InterfaceDTO

counter = Counter()


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
        conflicts = []
        mac_map: dict[
            str,
            list[
                tuple[
                    DataCenterAsset | None,
                    DataCenterAsset | None,
                    DataCenterAsset | None,
                    str | None,
                ]
            ],
        ] = defaultdict(list)

        def _match_remote_asset(interface: InterfaceDTO) -> dict:
            dic = interface.model_dump(
                exclude={
                    "vlans",
                    "native_vlan",
                    "mtu",
                    "name_cfg",
                    "speed",
                    "remote_id",
                    "remote_port",
                    "desc",
                    "remote_name",
                }
            )
            rm = RemoteAsset.from_interface_dto(interface)
            counter[rm.remote_mac_from_remote_id] += 1
            from_name, from_desc, from_eth = extract_asset(rm)
            if mac := rm.remote_mac_from_remote_id:
                mac_map[mac].append(
                    (from_name, from_desc, from_eth, interface.remote_port)
                )
            cv = {True: "OK", False: "CONFLICT!", None: "None"}[
                cross_validate(from_name, from_desc, from_eth)
            ]
            if cv == "CONFLICT!":
                conflicts.append(
                    {
                        "interface": interface,
                        "remote_asset": rm,
                        "from_name": from_name,
                        "from_desc": from_desc,
                        "from_eth": from_eth,
                    }
                )
            dic.update(
                {
                    "from_remote_name": from_name,
                    "from_desc": from_desc,
                    "from_eth": from_eth,
                    "cross_validate": cv,
                }
            )
            return dic

        dry_run: bool = options["dry_run"]

        switches: list[str] = self.backend.get_switches()
        dc6_switches = [s for s in switches if "sw1.dc6.alledc.net" in s]
        dc5_switches = [s for s in switches if "sw1.dc5.alledc.net" in s]
        dc4_switches = [s for s in switches if "sw1.dc4.local" in s]
        for switch_hostname in itertools.chain(
            dc4_switches, dc5_switches, dc6_switches
        ):  # switches:
            switch: SwitchDTO = self.backend.get_switchports(switch_hostname)
            with pl.Config(tbl_rows=500, tbl_cols=30, fmt_str_lengths=100):
                print(f"Switch: {switch.hostname}")
                print(
                    pl.DataFrame(
                        [_match_remote_asset(p) for p in reversed(switch.ports)]
                    )
                )

            if dry_run:
                continue
        #
        #     switch_instance: DataCenterAsset = self._get_switch(switch)
        #     for interface_dto in switch.ports:
        #         port = Port.objects.get_or_create(
        #             label=interface_dto.name, data_center_asset=switch_instance
        #         )[0]
        #         dca = self._get_remote_instance(interface_dto)
        #         if port and dca:
        #             remote_port = Port.objects.get_or_create(
        #                 label=interface_dto.remote_port, data_center_asset=dca
        #             )[0]
        #             connect(port, remote_port)
        #         else:
        #             print(
        #                 f"Could not connect port {interface_dto} to remote asset Port: {port}, DCA: {dca}"
        #             )
        # print("COUNTER")
        # print(counter)
        [
            print(
                conf["interface"].remote_id,
                {conf["from_name"], conf["from_desc"], conf["from_eth"]},
            )
            for conf in conflicts
        ]

        # Połączona analiza: MAC-i z 2 wpisami + konflikty + next_mac
        from ralph.assets.models import Ethernet
        from ralph.switchports.asset_matching import next_mac

        # Zbiór MAC-ów które mają conflict
        conflict_macs = {
            conf["remote_asset"].remote_mac_from_remote_id
            for conf in conflicts
            if conf["remote_asset"].remote_mac_from_remote_id
        }

        dual_mac_rows = []
        for mac, entries in mac_map.items():
            if len(entries) != 2:
                continue
            from_name_0, from_desc_0, from_eth_0, remote_port_0 = entries[0]
            from_name_1, from_desc_1, from_eth_1, remote_port_1 = entries[1]

            # next_mac lookup
            next_mac_val = next_mac(mac)
            try:
                this_eth: Ethernet = Ethernet.objects.get(mac=mac)
                other_eths: list[str] = [
                    eth.label
                    for eth in Ethernet.objects.filter(base_object=from_eth_0)
                    if eth != this_eth and eth is not None
                ]
            except:  # noqa
                this_eth = None
                other_eths = []
            try:
                next_eth = Ethernet.objects.get(mac=next_mac_val)
                next_mac_asset = DataCenterAsset.objects.get(id=next_eth.base_object.id)
            except (Ethernet.DoesNotExist, DataCenterAsset.DoesNotExist):
                next_mac_asset = None

            eth_count = (
                Ethernet.objects.filter(base_object=from_eth_0).count()
                if from_eth_0
                else None
            )

            if from_eth_0 and next_mac_asset:
                same_object = "True" if from_eth_0 == next_mac_asset else "False"
            elif from_eth_0 and not next_mac_asset:
                same_object = "2nd_missing"
            else:
                same_object = None

            # cross-validation per entry
            cv_0 = cross_validate(from_name_0, from_desc_0, from_eth_0)
            cv_1 = cross_validate(from_name_1, from_desc_1, from_eth_1)
            cv_map = {True: "OK", False: "CONFLICT", None: "None"}

            dual_mac_rows.append(
                {
                    "mac": mac,
                    "next_mac": next_mac_val,
                    "from_eth": str(from_eth_0) if from_eth_0 else None,
                    "next_mac_asset": str(next_mac_asset) if next_mac_asset else None,
                    "same_object": same_object,
                    "eth_count": eth_count,
                    "cv_0": cv_map[cv_0],
                    "cv_1": cv_map[cv_1],
                    "from_name_0": str(from_name_0) if from_name_0 else None,
                    "from_name_1": str(from_name_1) if from_name_1 else None,
                    "port_0": remote_port_0,
                    "port_1": remote_port_1,
                    "has_conflict": mac in conflict_macs,
                    "this_eth": this_eth.label if this_eth else None,
                    "other_eths": ", ".join(
                        [eth for eth in other_eths if eth is not None]
                    )
                    if other_eths
                    else None,
                }
            )

        try:
            if dual_mac_rows:
                with pl.Config(tbl_rows=500, tbl_cols=30, fmt_str_lengths=120):
                    df = pl.DataFrame(dual_mac_rows)
                    print("Dual MACs with 2 entries:")
                    print(df)
                    df.write_csv("dual_mac_analysis.csv")
        except:  # noqa
            pass

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
