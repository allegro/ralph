# -*- coding: utf-8 -*-
"""
Transition actions connected with security.

"""

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from ralph.data_center.models import DataCenterAsset
from ralph.lib.transitions.decorators import transition_action
from ralph.virtual.models import CloudHost, VirtualServer

HOST_MODELS = [DataCenterAsset, CloudHost, VirtualServer]


@transition_action(verbose_name=_("Cleanup security scans"), models=HOST_MODELS)
def cleanup_security_scans(cls, instances, **kwargs):
    with transaction.atomic():
        for instance in instances:
            try:
                instance.securityscan.delete()
            except cls.securityscan.RelatedObjectDoesNotExist:
                pass
