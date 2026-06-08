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
            help="Write the generated Mermaid graph to a file instead of stdout.",
        )
        parser.add_argument(
            "--direction",
            choices=["LR", "RL", "TB", "BT"],
            default="LR",
            help="Mermaid graph direction.",
        )

    def handle(self, *args, **options):
        graph = build_mermaid_graph(
            get_connections(options["hostnames"]),
            direction=options["direction"],
        )
        output = options.get("output")
        if not output:
            self.stdout.write(graph)
            return

        output_path = Path(output)
        if output_path.parent != Path(".") and not output_path.parent.exists():
            raise CommandError(f"Output directory does not exist: {output_path.parent}")
        output_path.write_text(graph, encoding="utf-8")
        self.stdout.write(f"Saved graph to {output_path}")


def get_connections(hostnames: list[str]) -> list[Connection]:
    queryset = Connection.objects.prefetch_related(
        "members__port__data_center_asset"
    ).order_by("id")
    if hostnames:
        queryset = queryset.filter(
            members__port__data_center_asset__hostname__in=hostnames
        ).distinct()
    return list(queryset)


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
