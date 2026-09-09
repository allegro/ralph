"""Switchport models, grouped by bounded context.

Import paths stay flat on purpose: ``from ralph.switchports.models import Port``
keeps working for admin, api, migrations and every external consumer. The
actual definitions live in focused submodules:

* ``connections`` — Port / Connection / ConnectionMember / AddressReservation
* ``rack_config`` — RackConfiguration / RackSwitchConfiguration / ...Override
* ``validation``  — BackendValidationResult / SwitchportRefreshJob + enums
"""

from ralph.switchports.models.connections import (
    AddressReservation,
    Connection,
    ConnectionMember,
    Port,
)
from ralph.switchports.models.rack_config import (
    RackConfiguration,
    RackSwitchConfiguration,
    RackSwitchConfigurationOverride,
)
from ralph.switchports.models.validation import (
    BackendValidationResult,
    DiffEntry,
    RefreshJobStatus,
    SwitchportRefreshJob,
    ValidationStatus,
)

__all__ = [
    "AddressReservation",
    "BackendValidationResult",
    "Connection",
    "ConnectionMember",
    "DiffEntry",
    "Port",
    "RackConfiguration",
    "RackSwitchConfiguration",
    "RackSwitchConfigurationOverride",
    "RefreshJobStatus",
    "SwitchportRefreshJob",
    "ValidationStatus",
]
