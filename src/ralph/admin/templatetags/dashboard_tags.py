# -*- coding: utf-8 -*-
from collections import Counter, Iterable
from itertools import cycle

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Count, Prefetch, Q, Sum
from django.template import Library
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import BaseObject, Service, ServiceEnvironment
from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models import (
    DataCenter,
    DataCenterAsset,
    Rack,
    RackAccessory
)

register = Library()
COLORS = ['green', 'blue', 'purple', 'orange', 'red', 'pink']


def get_user_equipment_tile_data(user):
    return {
        'class': 'my-equipment',
        'label': _('Your equipment'),
        'count': BackOfficeAsset.objects.filter(
            Q(user=user) | Q(owner=user)
        ).count(),
        'url': reverse('current_user_info'),
    }


def get_user_equipment_to_accept_tile_data(user):
    from ralph.accounts.helpers import get_assets_to_accept, get_acceptance_url
    assets_to_accept_count = get_assets_to_accept(user).count()
    if not assets_to_accept_count:
        return None
    return {
        'class': 'equipment-to-accept',
        'label': _('Equipments to accept'),
        'count': assets_to_accept_count,
        'url': get_acceptance_url(user),
    }


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


@register.inclusion_tag(
    'admin/templatetags/dc_capacity.html', takes_context=True
)
def dc_capacity(context, data_centers=None, size='big'):
    user = context.request.user
    if not user.has_perm('data_center.view_datacenter'):
        return {}
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


@register.inclusion_tag(
    'admin/templatetags/ralph_summary.html', takes_context=True
)
def ralph_summary(context):
    user = context.request.user
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
        if not user.has_perm('{}.view_{}'.format(app, meta.model_name)):
            continue
        results.append({
            'label': meta.verbose_name_plural,
            'count': model.objects.count(),
            'class': slugify(meta.model_name),
            'icon': 'icon',
            'url': reverse('admin:{}_{}_changelist'.format(
                meta.app_label, meta.model_name
            ))
        })
    results.append(get_user_equipment_tile_data(user=user))
    accept_tile_data = get_user_equipment_to_accept_tile_data(user=user)
    if accept_tile_data:
        results.append(accept_tile_data)
    return {'results': results}


@register.inclusion_tag('admin/templatetags/my_services.html')
def my_services(user):
    return {
        'services': Service.objects.prefetch_related(
            Prefetch(
                'serviceenvironment_set',
                queryset=ServiceEnvironment.objects.prefetch_related(
                    Prefetch(
                        'baseobject_set',
                        queryset=BaseObject.objects.order_by('content_type_id')
                    )
                )
            ),
            'serviceenvironment_set__environment',
        ).filter(technical_owners=user, active=True),
        'user': user
    }


@register.inclusion_tag('admin/templatetags/objects_summary.html')
def get_objects_summary(service_env, content_type_id, objects):
    from django.core.urlresolvers import reverse
    content_type = ContentType.objects.get_for_id(content_type_id)
    opts = content_type.model_class()._meta
    url = reverse(
        'admin:{}_{}_changelist'.format(opts.app_label, opts.model_name)
    )
    return {
        'url': '{}?service_env={}'.format(url, service_env.id),
        'name': opts.verbose_name,
        'count': len(objects),
    }
