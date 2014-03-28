#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select import LookupChannel

from django.utils.html import escape
from django.db.models import Q

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

    # change management types
    CIChange,
    CIChangeZabbixTrigger,
    CIChangeCMDBHistory,
    CIChangeGit,
    CIChangePuppet,
    GitPathMapping,

    # puppet logger types
    PuppetLog,

    CIEvent,
    CIProblem,
    CIIncident,
    JiraChanges,

    ArchivedCIChangeZabbixTrigger,
    ArchivedCIChangeCMDBHistory,
    ArchivedCIChange,
    ArchivedCIChangeGit,
    ArchivedCIChangePuppet,
    ArchivedPuppetLog,
)

from ralph.cmdb.models_audits import (
    Auditable,
    AuditStatus,
)

__all__ = [
    # constants
    'CI_RELATION_TYPES',
    'CI_STATE_TYPES',
    'CI_STATUS_TYPES',
    'CI_ATTRIBUTE_TYPES',
    'CI_CHANGE_TYPES',
    'CI_CHANGE_PRIORITY_TYPES',
    'CI_TYPES',
    'CI_CHANGE_REGISTRATION_TYPES',

    # base types
    'CI',
    'CIRelation',
    'CILayer',
    'CIType',
    'CIAttribute',
    'CIValueDate',
    'CIValueInteger',
    'CIValueFloat',
    'CIValueString',
    'CIValueChoice',
    'CIContentTypePrefix',

    # owners
    'CIOwner',
    'CIOwnershipType',

    # change management types
    'CIChange',
    'CIChangeZabbixTrigger',
    'CIChangeCMDBHistory',
    'CIChangeGit',
    'CIChangePuppet',
    'GitPathMapping',

    # puppet logger types
    'PuppetLog',
    'CIAttributeValue',
    'CIEvent',
    'CIProblem',
    'CIIncident',
    'JiraChanges',

    # audits
    'Auditable',
    'AuditStatus',

    'ArchivedCIChangeZabbixTrigger',
    'ArchivedCIChangeCMDBHistory',
    'ArchivedCIChange',
    'ArchivedCIChangeGit',
    'ArchivedCIChangePuppet',
    'ArchivedPuppetLog',
]

# hook signals, don't remove this.
import ralph.cmdb.models_signals  # noqa


class CILookup(LookupChannel):
    model = CI

    def get_query(self, query, request):
        return CI.objects.filter(
            Q(name__istartswith=query.strip())
        ).order_by('name')[:10]

    def get_result(self, obj):
        return obj.name

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return '<b>{}</b> ({})<div><i>{}</i></div>'.format(
            escape(obj.name),
            escape(str(obj.content_object)),
            escape(obj.type),
        )
