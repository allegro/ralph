# -*- coding: utf-8 -*-
from django.db import models

from ralph.lib.mixins.models import TaggableMixin, TimeStampMixin
from ralph.lib.permissions import PermByFieldMixin
from ralph.lib.permissions.models import PermissionsBase
from ralph.lib.polymorphic.models import Polymorphic, PolymorphicBase
from ralph.lib.transitions import TransitionWorkflowBase

BaseObjectMeta = type(
    'BaseObjectMeta', (
        PolymorphicBase,
        PermissionsBase,
        TransitionWorkflowBase
    ), {}
)


class BaseObject(
    Polymorphic,
    TaggableMixin,
    PermByFieldMixin,
    TimeStampMixin,
    models.Model,
    metaclass=BaseObjectMeta
):

    """Base object mixin."""

    parent = models.ForeignKey('self', null=True, blank=True)
    remarks = models.TextField(blank=True)
    service_env = models.ForeignKey('ServiceEnvironment', null=True)
