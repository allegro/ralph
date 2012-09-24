#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from ralph.cmdb.models_ci import (
    # constants
    CI_RELATION_TYPES,
    CI_STATE_TYPES,
    CI_STATUS_TYPES,
    CI_ATTRIBUTE_TYPES,
    CI_TYPES,

    # base types
    CI,
    CIRelation,
    CILayer,
    CIType,
    CIAttribute,
    CIValueDate,
    CIValueInteger,
    CIValueFloat,
    CIValueString,
    CIValueChoice,
    CIContentTypePrefix,
    CIAttributeValue,

    CIOwner,
    CIOwnershipType,
)

from ralph.cmdb.models_changes import (
    CI_CHANGE_TYPES,
    CI_CHANGE_PRIORITY_TYPES,
    CI_CHANGE_REGISTRATION_TYPES,
    REGISTER_CHANGE_TYPES,

    # change management types
    CIChange,
    CIChangeZabbixTrigger,
    CIChangeStatusOfficeIncident,
    CIChangeCMDBHistory,
    CIChangeGit,
    CIChangePuppet,
    # puppet logger types
    PuppetLog,
    PuppetResourceStatus,
    CIEvent,
    CIProblem,
    CIIncident
)

from ralph.cmdb.models_audits import (
    Auditable,
    AuditStatus,
)

__all__ = [
    # constants
    CI_RELATION_TYPES,
    CI_STATE_TYPES,
    CI_STATUS_TYPES,
    CI_ATTRIBUTE_TYPES,
    CI_CHANGE_TYPES,
    CI_CHANGE_PRIORITY_TYPES,
    CI_TYPES,
    CI_CHANGE_REGISTRATION_TYPES,
    REGISTER_CHANGE_TYPES,

    #base types
    CI,
    CIRelation,
    CILayer,
    CIType,
    CIAttribute,
    CIValueDate,
    CIValueInteger,
    CIValueFloat,
    CIValueString,
    CIValueChoice,
    CIContentTypePrefix,

    # owners
    CIOwner,
    CIOwnershipType,

    #change management types
    CIChange,
    CIChangeZabbixTrigger,
    CIChangeStatusOfficeIncident,
    CIChangeCMDBHistory,
    CIChangeGit,
    CIChangePuppet,

    #puppet logger types
    PuppetLog,
    PuppetResourceStatus,
    CIAttributeValue,
    CIEvent,
    CIProblem,
    CIIncident,

    #audit
    Auditable,
    AuditStatus,
]

# hook signals, don't remove this.
import ralph.cmdb.models_signals

