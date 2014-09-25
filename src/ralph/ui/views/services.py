# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.menu import MenuItem
from collections import OrderedDict

from ralph.account.models import Perm
from ralph.cmdb.models import CI_TYPES, CI_RELATION_TYPES, CIRelation
from ralph.discovery.models import Device
from ralph.ui.views.common import (
    Addresses,
    Asset,
    BaseMixin,
    Components,
    History,
    Info,
    Software,
    Scan,
)
from ralph.ui.views.devices import BaseDeviceList


class SerivcesSidebar(object):
    submodule_name = 'services'

    def __init__(self, *args, **kwargs):
        super(SerivcesSidebar, self).__init__(*args, **kwargs)
        self.businessline_id = None
        self.service_id = None
        self.environment_id = None

    def _get_tree(self):
        # get data
        business_service = CIRelation.objects.filter(
            parent__type_id=CI_TYPES.BUSINESSLINE,
            child__type_id=CI_TYPES.SERVICE,
            type=CI_RELATION_TYPES.CONTAINS,
        ).values_list(
            'parent__id',
            'parent__name',
            'child__id',
            'child__name',
        )
        business_profitcenter = CIRelation.objects.filter(
            parent__type_id=CI_TYPES.BUSINESSLINE,
            child__type_id=CI_TYPES.PROFIT_CENTER,
            type=CI_RELATION_TYPES.CONTAINS,
        ).values_list(
            'parent__id',
            'parent__name',
            'child__id',
        )
        profitcenter_service = CIRelation.objects.filter(
            parent__type_id=CI_TYPES.PROFIT_CENTER,
            child__type_id=CI_TYPES.SERVICE,
            type=CI_RELATION_TYPES.CONTAINS,
        ).values_list('parent__id', 'child__id', 'child__name')
        service_environment = CIRelation.objects.filter(
            parent__type_id=CI_TYPES.SERVICE,
            child__type_id=CI_TYPES.ENVIRONMENT,
            type=CI_RELATION_TYPES.CONTAINS,
        ).values_list('parent__id', 'child__id', 'child__name')
        # make tree
        tree = {}
        pc_bl_map = {}  # profit_center -> business line
        for p_id, p_name, c_id in business_profitcenter:
            tree.setdefault(
                p_id,
                {
                    'name': p_name,
                    'type': 'business_line',
                    'childs': {},
                }
            )
            pc_bl_map[c_id] = p_id
        s_bl_map = {}  # service -> business line
        for p_id, c_id, c_name in profitcenter_service:
            if p_id not in pc_bl_map:
                continue
            tree[pc_bl_map[p_id]]['childs'].setdefault(
                c_id,
                {
                    'name': c_name,
                    'type': 'service',
                    'childs': {},
                }
            )
            s_bl_map[c_id] = pc_bl_map[p_id]
        for p_id, p_name, c_id, c_name in business_service:
            tree.setdefault(
                p_id,
                {
                    'name': p_name,
                    'type': 'business_line',
                    'childs': {
                        c_id: {
                            'name': c_name,
                            'type': 'service',
                            'childs': {}
                        }
                    },
                }
            )['childs'].setdefault(
                c_id,
                {
                    'name': c_name,
                    'type': 'service',
                    'childs': {}
                }
            )
            s_bl_map[c_id] = p_id
        for p_id, c_id, c_name in service_environment:
            if p_id not in s_bl_map:
                continue
            if p_id not in tree[s_bl_map[p_id]]['childs']:
                continue
            tree[s_bl_map[p_id]]['childs'][p_id]['childs'].setdefault(
                c_id,
                {
                    'name': c_name,
                    'type': 'environment',
                }
            )
        # sorting
        for bl_key, bl_value in tree.iteritems():
            for s_key, s_value in bl_value['childs'].iteritems():
                s_value['childs'] = OrderedDict(
                    sorted(
                        s_value['childs'].items(),
                        key=lambda k: k[1]['name']
                    )
                )
            bl_value['childs'] = OrderedDict(
                sorted(
                    bl_value['childs'].items(),
                    key=lambda k: k[1]['name']
                )
            )
        tree = OrderedDict(
            sorted(
                tree.items(),
                key=lambda k: k[1]['name']
            )
        )
        return tree

    def _get_menu(self, tree):
        items = []
        for bl_id, bl_data in tree.iteritems():
            bl_item = MenuItem(
                label=bl_data['name'],
                name='businessline_%s' % bl_id,
                fugue_icon='fugue-tie',
                view_name='services',
                view_args=['bl-%s' % bl_id],
                indent=' ',
                collapsible=True,
                collapsed=False if self.businessline_id == str(bl_id) else True
            )
            bl_item.subitems = []
            for s_id, s_data in bl_data.get('childs', {}).iteritems():
                s_item = MenuItem(
                    label=s_data['name'],
                    name='service_%s' % s_id,
                    fugue_icon='fugue-disc-share',
                    view_name='services',
                    view_args=['bl-%s' % bl_id, 'ser-%s' % s_id],
                    indent=' ',
                    collapsible=True,
                    collapsed=False if self.service_id == str(s_id) else True
                )
                s_item.subitems = []
                for e_id, e_data in s_data.get('childs', {}).iteritems():
                    e_item = MenuItem(
                        label=e_data['name'],
                        name='env_%s' % e_id,
                        fugue_icon='fugue-tree',
                        view_name='services',
                        view_args=[
                            'bl-%s' % bl_id, 'ser-%s' % s_id, 'env-%s' % e_id
                        ],
                        indent=' '
                    )
                    e_item.parent = s_item
                    s_item.subitems.append(e_item)
                s_item.parent = bl_item
                bl_item.subitems.append(s_item)
            items.append(bl_item)
        return items

    def _set_request_params(self):
        if self.kwargs.get('businessline_id'):
            self.businessline_id = self.kwargs['businessline_id'].replace(
                'bl-', ''
            )
        if self.kwargs.get('service_id'):
            self.service_id = self.kwargs['service_id'].replace('ser-', '')
        if self.kwargs.get('environment_id'):
            self.environment_id = self.kwargs['environment_id'].replace(
                'env-', ''
            )

    def get_context_data(self, **kwargs):
        ret = super(SerivcesSidebar, self).get_context_data(**kwargs)
        self._set_request_params()
        sidebar_selected = None
        if self.environment_id:
            sidebar_selected = 'env_%s' % self.environment_id
        elif self.service_id:
            sidebar_selected = 'service_%s' % self.service_id
        elif self.businessline_id:
            sidebar_selected = 'businessline_%s' % self.businessline_id
        ret.update({
            'sidebar_items': self._get_menu(self._get_tree()),
            'sidebar_selected': sidebar_selected,
            'section': 'services',
            'show_tab_menu': True,
        })
        return ret


class ServicesDeviceList(SerivcesSidebar, BaseMixin, BaseDeviceList):

    def user_allowed(self):
        self._set_request_params()
        has_perm = self.request.user.get_profile().has_perm
        return has_perm(Perm.list_devices_generic)

    def _get_businessline_services_ids(self, businessline_id):
        services_ids = set(
            CIRelation.objects.filter(
                parent_id=businessline_id,
                parent__type_id=CI_TYPES.BUSINESSLINE,
                child__type_id=CI_TYPES.SERVICE,
                type=CI_RELATION_TYPES.CONTAINS,
            ).values_list(
                'child__id',
                flat=True
            )
        )
        services_ids.update(
            set(
                CIRelation.objects.filter(
                    parent_id__in=CIRelation.objects.filter(
                        parent_id=businessline_id,
                        parent__type_id=CI_TYPES.BUSINESSLINE,
                        child__type_id=CI_TYPES.PROFIT_CENTER,
                        type=CI_RELATION_TYPES.CONTAINS,
                    ).values_list(
                        'child__id',
                        flat=True
                    ),
                    parent__type_id=CI_TYPES.PROFIT_CENTER,
                    child__type_id=CI_TYPES.SERVICE,
                    type=CI_RELATION_TYPES.CONTAINS,
                ).values_list('child__id', flat=True)
            )
        )
        return services_ids

    def get_queryset(self):
        if self.environment_id:
            queryset = Device.objects.filter(
                device_environment_id=self.environment_id
            )
        elif self.service_id:
            queryset = Device.objects.filter(
                service_id=self.service_id
            )
        elif self.businessline_id:
            queryset = Device.objects.filter(
                service_id__in=self._get_businessline_services_ids(
                    self.businessline_id
                )
            )
        else:
            queryset = Device.objects.all()
        return self.sort_queryset(queryset)


class Services(SerivcesSidebar, BaseMixin):
    submodule_name = 'services'


class ServicesInfo(Services, Info):
    pass


class ServicesComponents(Services, Components):
    pass


class ServicesSoftware(Services, Software):
    pass


class ServicesAddresses(Services, Addresses):
    pass


class ServicesHistory(Services, History):
    pass


class ServicesAsset(Services, Asset):
    pass


class ServicesScan(Services, Scan):
    submodule_name = 'services'
