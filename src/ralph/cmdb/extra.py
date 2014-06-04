# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

"""Extras to be used via DI mechanism."""

from django.template.loader import render_to_string

from ralph.cmdb.models_ci import CI, CIOwnership


def ralph_obj_owner_table(device):
    """Renders a table containing owners of a given ralph object."""
    ci = CI.get_by_content_object(device)
    ownerships = CIOwnership.objects.filter(ci=ci)
    if not ci:
        return ''
    return render_to_string(
        'cmdb/ralph_obj_owner_table.html',
        {'ownerships': ownerships},
    )
