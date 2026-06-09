from collections.abc import Iterable
from pathlib import Path

from django.core.management import BaseCommand, CommandError

from ralph.switchports.models import Connection, Port


class Command(BaseCommand):
    help = "Generate a Mermaid graph for switchport connections."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hostname",
            action="append",
            dest="hostnames",
            default=[],
            help="Limit graph to connections touching the given hostname. Repeatable.",
        )
        parser.add_argument(
            "--output",
            help="Write the generated graph to a file instead of stdout.",
        )
        parser.add_argument(
            "--direction",
            choices=["LR", "RL", "TB", "BT"],
            default="LR",
            help="Mermaid graph direction.",
        )
        parser.add_argument(
            "--depth",
            type=int,
            default=1,
            help=(
                "Neighborhood depth for --hostname filtering. "
                "1 means direct connections, 2 includes neighbors of neighbors, etc."
            ),
        )

    def handle(self, *args, **options):
        depth = options["depth"]
        if depth < 1:
            raise CommandError("--depth must be >= 1")

        content = build_mermaid_graph(
            get_connections(options["hostnames"], depth=depth),
            direction=options["direction"],
        )

        output = options.get("output")
        if not output:
            self.stdout.write(content)
            return

        output_path = Path(output)
        if output_path.parent != Path(".") and not output_path.parent.exists():
            raise CommandError(f"Output directory does not exist: {output_path.parent}")
        output_path.write_text(content, encoding="utf-8")
        self.stdout.write(f"Saved graph to {output_path}")


def get_connections(hostnames: list[str], depth: int = 1) -> list[Connection]:
    queryset = Connection.objects.prefetch_related(
        "members__port__data_center_asset"
    ).order_by("id")
    if not hostnames:
        return list(queryset)

    seed_assets = set(
        Port.objects.filter(data_center_asset__hostname__in=hostnames)
        .values_list("data_center_asset_id", flat=True)
        .distinct()
    )
    if not seed_assets:
        return []

    visited_assets = set(seed_assets)
    frontier = set(seed_assets)
    connection_ids: set[int] = set()

    for _ in range(depth):
        if not frontier:
            break

        level_connection_ids = set(
            Connection.objects.filter(members__port__data_center_asset_id__in=frontier)
            .values_list("id", flat=True)
            .distinct()
        )
        new_connection_ids = level_connection_ids - connection_ids
        if not new_connection_ids:
            break

        connection_ids.update(new_connection_ids)

        neighbor_assets = set(
            Port.objects.filter(connectionmember__connection_id__in=new_connection_ids)
            .values_list("data_center_asset_id", flat=True)
            .distinct()
        )
        frontier = neighbor_assets - visited_assets
        visited_assets.update(neighbor_assets)

    if not connection_ids:
        return []

    return list(queryset.filter(id__in=connection_ids))


# ---------------------------------------------------------------------------
# Mermaid output
# ---------------------------------------------------------------------------


def build_mermaid_graph(
    connections: Iterable[Connection], direction: str = "LR"
) -> str:
    lines = [f"graph {direction}"]
    emitted_assets: set[int] = set()
    has_connections = False

    for connection in connections:
        members = sorted(connection.members.all(), key=_member_sort_key)
        if not members:
            continue

        has_connections = True
        if len(members) == 2:
            left, right = members
            lines.extend(_asset_node_lines(left.port, emitted_assets))
            lines.extend(_asset_node_lines(right.port, emitted_assets))
            edge_label = escape_mermaid_label(f"{left.port.label} ↔ {right.port.label}")
            lines.append(
                f'    {asset_node_id(left.port)} <-->|"{edge_label}"| {asset_node_id(right.port)}'
            )
            continue

        hub_id = connection_node_id(connection)
        lines.append(f'    {hub_id}{{"{connection_label(connection)}"}}')
        for member in members:
            lines.extend(_asset_node_lines(member.port, emitted_assets))
            port_name = escape_mermaid_label(member.port.label)
            lines.append(
                f'    {asset_node_id(member.port)} ---|"{port_name}"| {hub_id}'
            )

    if not has_connections:
        lines.append('    empty["No switchport connections found"]')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _member_sort_key(member) -> tuple[str, str, int]:
    return (
        member.port.data_center_asset.hostname,
        member.port.label,
        member.port_id,
    )


def _asset_node_lines(port: Port, emitted_assets: set[int]) -> list[str]:
    asset = port.data_center_asset
    if asset.pk in emitted_assets:
        return []
    emitted_assets.add(asset.pk)
    hostname = escape_mermaid_label(asset.hostname or f"asset_{asset.pk}")
    return [f'    {asset_node_id(port)}["{hostname}"]']


def asset_node_id(port: Port) -> str:
    return f"asset_{port.data_center_asset_id}"


def connection_node_id(connection: Connection) -> str:
    return f"connection_{connection.pk}"


def connection_label(connection: Connection) -> str:
    return f"Connection #{connection.pk}"


def escape_mermaid_label(value: str) -> str:
    return value.replace('"', "'")
