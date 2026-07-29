"""Physical connection graph operations.

``connect`` / ``disconnect`` plus the pluggable strategies. The public surface
is re-exported here so ``from ralph.switchports.connections import connect``
keeps working after the module became a package.
"""

from ralph.switchports.connections.planning import switch_port_owner
from ralph.switchports.connections.strategies import (
    ConnectionAlreadyExistsException,
    ConnectionStrategy,
    DefaultConnectionStrategy,
    NondestructiveConnectionStrategy,
    connect,
    default_strategy,
    disconnect,
)

__all__ = [
    "ConnectionAlreadyExistsException",
    "ConnectionStrategy",
    "DefaultConnectionStrategy",
    "NondestructiveConnectionStrategy",
    "connect",
    "default_strategy",
    "disconnect",
    "switch_port_owner",
]
