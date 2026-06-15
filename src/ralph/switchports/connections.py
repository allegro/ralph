import abc

from django.db import transaction

from ralph.switchports.models import Port, Connection, ConnectionMember


class ConnectionAlreadyExistsException(Exception):
    pass


class ConnectionStrategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def connect(self, port1: Port, port2: Port) -> tuple[Connection, bool]:
        """
        Create a connection between two ports.
        Returns a tuple of the created Connection and a boolean indicating whether any new connections were created
        """
        raise NotImplementedError("Subclasses must implement this method.")


class DefaultConnectionStrategy(ConnectionStrategy):
    """
    Strategy for creating connections between ports.
    """

    def connect(self, port1: Port, port2: Port) -> tuple[Connection, bool]:
        """
        Connect two ports together. Delete all other connections for these ports.
        """
        with transaction.atomic():
            _lock_ports(port1, port2)
            connections1 = list(Connection.objects.filter(members__port=port1))
            connections2 = list(Connection.objects.filter(members__port=port2))
            if len(connections1) != 1 or len(connections2) != 1:
                Connection.objects.filter(
                    id__in=[c.id for c in connections1 + connections2]
                ).delete()
                return _create_connection(port1, port2), True

            c1 = connections1[0]
            c2 = connections2[0]
            if c1 == c2:
                return c1, False
            else:
                c1.delete()
                c2.delete()
                return _create_connection(port1, port2), True


class NondestructiveConnectionStrategy(ConnectionStrategy):
    """
    Strategy for creating connections between ports without deleting existing connections.
    """

    def connect(self, port1: Port, port2: Port) -> tuple[Connection, bool]:
        """
        Connect two ports together. If either port is already connected to any other port,
        an exception will be raised to prevent deletion of existing connections.
        """
        with transaction.atomic():
            _lock_ports(port1, port2)
            connections1 = list(Connection.objects.filter(members__port=port1))
            connections2 = list(Connection.objects.filter(members__port=port2))
            if (
                len(connections1) == 1
                and len(connections2) == 1
                and connections1[0] == connections2[0]
            ):
                return connections1[0], False
            elif connections1 or connections2:
                raise ConnectionAlreadyExistsException(
                    f"Cannot connect {port1} and {port2} because one or both ports are already connected to other ports."
                )
            else:
                return _create_connection(port1, port2), True


def _lock_ports(*ports: Port) -> None:
    """Lock ports to prevent race conditions"""
    list(
        Port.objects.filter(id__in=[p.id for p in ports])
        .order_by("id")
        .select_for_update()
    )


def _create_connection(port1: Port, port2: Port) -> Connection:
    connection = Connection.objects.create()
    ConnectionMember.objects.create(connection=connection, port=port1)
    ConnectionMember.objects.create(connection=connection, port=port2)
    return connection


default_strategy = DefaultConnectionStrategy()


def connect(
    port1: Port, port2: Port, strategy: ConnectionStrategy = default_strategy
) -> tuple[Connection, bool]:
    """
    Create a connection between two ports.
    Returns a tuple of the created Connection and a boolean indicating whether any new connections were created
    """
    return strategy.connect(port1, port2)


def disconnect(*ports: Port) -> None:
    """Disconnect ports by deleting any connections"""
    with transaction.atomic():
        _lock_ports(*ports)
        Connection.objects.filter(members__port__in=ports).delete()
