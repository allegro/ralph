# -*- coding: utf-8 -*-
from collections import Counter, Iterable
from itertools import cycle

from django.apps import apps
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.template import Library
from django.utils.text import slugify

from ralph.data_center.models import (
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory
)

register = Library()

COLORS = ['green', 'blue', 'purple', 'orange', 'red', 'pink']


def get_available_space_in_data_centers(data_centers):
    available = Rack.objects.filter(
        server_room__data_center__in=data_centers,
        require_position=True
    ).values_list(
        'server_room__data_center__name'
    ).annotate(
        s=Sum('max_u_height')
    )
    return Counter(dict(available))


def get_used_space_in_data_centers(data_centers):
    used_by_accessories = RackAccessory.objects.filter(
        rack__server_room__data_center__in=data_centers,
    ).values_list(
        'rack__server_room__data_center__name'
    ).annotate(
        s=Count('rack')
    )
    used_by_assets = DataCenterAsset.objects.filter(
        rack__server_room__data_center__in=data_centers,
        model__has_parent=False,
        rack__require_position=True
    ).values_list(
        'rack__server_room__data_center__name'
    ).annotate(
        s=Sum('model__height_of_device')
    )
    return Counter(dict(used_by_assets)) + Counter(dict(used_by_accessories))


@register.inclusion_tag('admin/templatetags/dc_capacity.html')
def dc_capacity(data_centers=None, size='big'):
    color = cycle(COLORS)
    if not data_centers:
        data_centers = DataCenter.objects.all()
    if not isinstance(data_centers, Iterable):
        data_centers = [data_centers]
    data_centers_mapper = dict(data_centers.values_list('name', 'id'))
    available_space = get_available_space_in_data_centers(data_centers)
    used_space = get_used_space_in_data_centers(data_centers)
    difference = dict(available_space - used_space)
    results = []
    for name, value in sorted(difference.items()):
        capacity = 100 - (100 * value / available_space[name])
        tooltip = '<strong>Free U:</strong> {} ({} in total)'.format(
            available_space[name] - int(used_space[name]),
            available_space[name]
        )
        results.append({
            'url': '{}#/dc/{}'.format(
                reverse('dc_view'), data_centers_mapper[name]
            ),
            'tooltip': tooltip,
            'size': size,
            'color': next(color),
            'dc': name,
            'capacity': int(capacity)
        })
    return {'capacities': results}


@register.inclusion_tag('admin/templatetags/ralph_summary.html')
def ralph_summary():
    models = [
        'data_center.DataCenterAsset',
        'back_office.BackOfficeAsset',
        'licences.Licence',
        'supports.Support',
        'domains.Domain',
        'accounts.RalphUser',
    ]
    results = []
    for model_name in models:
        app, model = model_name.split('.')
        model = apps.get_model(app, model)
        meta = model._meta
        results.append({
            'label': meta.verbose_name_plural,
            'count': model.objects.count(),
            'class': slugify(meta.verbose_name_plural),
            'icon': 'icon',
            'url_name': 'admin:{}_{}_changelist'.format(
                meta.app_label, meta.model_name
            )

        })
    return {'results': results}
