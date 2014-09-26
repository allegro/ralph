# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

"""Extras to be used via DI mechanism."""

from django.core.urlresolvers import reverse_lazy
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from ralph.cmdb.models_ci import CI, CIOwner, CIOwnership, CIOwnershipType


def ralph_device_owner_table(device):
    """Renders a table containing owners of a given ralph device object."""
    context = {
        'venture': device.venture,
        'venture_business': [],
        'venture_technical': [],
        'service_business': [],
        'service_technical': [],
    }
    if device.venture:
        venture_ci = CI.get_by_content_object(device.venture)
        venture_ownerships = CIOwnership.objects.filter(ci=venture_ci)
        context['venture_business'] = venture_ownerships.filter(
            type=CIOwnershipType.business,
        )
        context['venture_technical'] = venture_ownerships.filter(
            type=CIOwnershipType.technical,
        )
    if device.service:
        service_ownerships = CIOwnership.objects.filter(ci=device.service)
        context['service_business'] = service_ownerships.filter(
            type=CIOwnershipType.business,
        )
        context['service_technical'] = service_ownerships.filter(
            type=CIOwnershipType.technical,
        )
    return render_to_string('cmdb/ralph_device_owner_table.html', context)


def ralph_obj_owner_column_factory(type_):
    """Factory for admin column displaying ownership.

    :param type_: A string: either 'business' or 'technical'

    :return: A function to be used as table column
    """
    ownership_type, description = {
        'business': (CIOwnershipType.business, _('business owners')),
        'technical': (CIOwnershipType.technical, _('technical owners')),
    }[type_]
    # We can't use partials, because they don't bind. So we use a closure

    def result_fn(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        owners = CIOwner.objects.filter(
            ciownership__type=ownership_type,
            ci=ci
        )
        part_url = reverse_lazy('ci_edit', kwargs={'ci_id': str(ci.id)})
        link_text = (
            ", ".join([unicode(owner) for owner in owners])
            if owners
            else '[add]'
        )
        return "<a href=\"{}\">{}</a>".format(part_url, link_text)

    result_fn.short_description = description
    result_fn.allow_tags = True
    return result_fn


def ralph_obj_all_ownerships(obj):
    ci = CI.get_by_content_object(obj)
    if not ci:
        return []
    return CIOwnership.objects.filter(ci=ci)
