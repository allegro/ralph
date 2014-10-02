# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.menu import MenuItem
from collections import OrderedDict
from django.conf import settings

from ralph.account.models import Perm
from ralph.cmdb.models import (
    CI_RELATION_TYPES,
    CI_STATE_TYPES,
    CI_TYPES,
    CIAttributeValue,
    CIRelation,
)
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
from ralph.ui.views.reports import ReportDeviceList


SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE = getattr(
    settings,
    'SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE',
    False
)
ACTIVE_CIS_CONDITIONS = {
    'parent__state': CI_STATE_TYPES.ACTIVE,
    'child__state': CI_STATE_TYPES.ACTIVE,
}


def _get_calculated_in_scrooge_cis_ids():
    return CIAttributeValue.objects.filter(
        attribute__pk=7,
        value_boolean__value=True,
        ci__type=CI_TYPES.SERVICE,
    ).values_list('ci__pk', flat=True)


class SerivcesSidebar(object):
    submodule_name = 'services'

    def __init__(self, *args, **kwargs):
        super(SerivcesSidebar, self).__init__(*args, **kwargs)
        self.businessline_id = None
        self.service_id = None
        self.environment_id = None
        self.calc_in_scrooge_cis = None

    def _set_calc_in_scrooge_cis(self):
        if not SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE:
            self.calc_in_scrooge_cis = None
        if all((
            not self.calc_in_scrooge_cis,
            SHOW_ONLY_SERVICES_CALCULATED_IN_SCROOGE,
        )):
            self.calc_in_scrooge_cis = _get_calculated_in_scrooge_cis_ids()

    def _get_business_to_service(self, calculated_in_scrooge_cis=None):
        conditions = {
            'parent__type_id': CI_TYPES.BUSINESSLINE,
            'child__type_id': CI_TYPES.SERVICE,
            'type': CI_RELATION_TYPES.CONTAINS,
        }
        if calculated_in_scrooge_cis:
            conditions['child__id__in'] = calculated_in_scrooge_cis
        conditions.update(ACTIVE_CIS_CONDITIONS)
        return CIRelation.objects.filter(**conditions).values_list(
            'parent__id',
            'parent__name',
            'child__id',
            'child__name',
        )

    def _get_business_to_profitcenter(self):
        return CIRelation.objects.filter(
            parent__type_id=CI_TYPES.BUSINESSLINE,
            child__type_id=CI_TYPES.PROFIT_CENTER,
            type=CI_RELATION_TYPES.CONTAINS,
            **ACTIVE_CIS_CONDITIONS
        ).values_list(
            'parent__id',
            'parent__name',
            'child__id',
        )

    def _get_profitcenter_to_service(self, calculated_in_scrooge_cis=None):
        conditions = {
            'parent__type_id': CI_TYPES.PROFIT_CENTER,
            'child__type_id': CI_TYPES.SERVICE,
            'type': CI_RELATION_TYPES.CONTAINS,
        }
        if calculated_in_scrooge_cis:
            conditions['child__id__in'] = calculated_in_scrooge_cis
        conditions.update(ACTIVE_CIS_CONDITIONS)
        return CIRelation.objects.filter(**conditions).values_list(
            'parent__id',
            'child__id',
            'child__name',
        )

    def _get_service_to_environment(self, calculated_in_scrooge_cis=None):
        conditions = {
            'parent__type_id': CI_TYPES.SERVICE,
            'child__type_id': CI_TYPES.ENVIRONMENT,
            'type': CI_RELATION_TYPES.CONTAINS,
        }
        if calculated_in_scrooge_cis:
            conditions['parent__id__in'] = calculated_in_scrooge_cis
        conditions.update(ACTIVE_CIS_CONDITIONS)
        return CIRelation.objects.filter(**conditions).values_list(
            'parent__id',
            'child__id',
            'child__name',
        )

    def _merge_data_into_tree(
        self,
        business_service,
        business_profitcenter,
        profitcenter_service,
        service_environment,
    ):
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
        return tree

    def _sort_tree(self, tree):
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

    def _get_tree(self):
        # get data
        self._set_calc_in_scrooge_cis()
        business_service = self._get_business_to_service(
            self.calc_in_scrooge_cis,
        )
        business_profitcenter = self._get_business_to_profitcenter()
        profitcenter_service = self._get_profitcenter_to_service(
            self.calc_in_scrooge_cis,
        )
        service_environment = self._get_service_to_environment(
            self.calc_in_scrooge_cis,
        )
        # make tree
        tree = self._merge_data_into_tree(
            business_service,
            business_profitcenter,
            profitcenter_service,
            service_environment,
        )
        # sorting
        self._sort_tree(tree)
        return tree

    def _get_menu(self, tree):
        items = []
        for bl_id, bl_data in tree.iteritems():
            bl_item = MenuItem(
                label=bl_data['name'],
                name='bl_%s' % bl_id,
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
                    name='bl_%s_s_%s' % (bl_id, s_id),
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
                        name='bl_%s_s_%s_env_%s' % (bl_id, s_id, e_id),
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

    def _get_sidebar_selected(self):
        sidebar_selected = None
        if self.businessline_id:
            sidebar_selected = 'bl_%s' % self.businessline_id
            if self.service_id:
                sidebar_selected += '_s_%s' % self.service_id
                if self.environment_id:
                    sidebar_selected += '_env_%s' % self.environment_id
        return sidebar_selected

    def get_context_data(self, **kwargs):
        ret = super(SerivcesSidebar, self).get_context_data(**kwargs)
        self._set_request_params()
        ret.update({
            'sidebar_items': self._get_menu(self._get_tree()),
            'sidebar_selected': self._get_sidebar_selected(),
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
        self._set_calc_in_scrooge_cis()
        query = CIRelation.objects.filter(
            parent_id=businessline_id,
            parent__type_id=CI_TYPES.BUSINESSLINE,
            child__type_id=CI_TYPES.SERVICE,
            type=CI_RELATION_TYPES.CONTAINS,
            **ACTIVE_CIS_CONDITIONS
        )
        if self.calc_in_scrooge_cis:
            query = query.filter(child__id__in=self.calc_in_scrooge_cis)
        services_ids = set(query.values_list('child__id', flat=True))
        query = CIRelation.objects.filter(
            parent_id__in=CIRelation.objects.filter(
                parent_id=businessline_id,
                parent__type_id=CI_TYPES.BUSINESSLINE,
                child__type_id=CI_TYPES.PROFIT_CENTER,
                type=CI_RELATION_TYPES.CONTAINS,
                **ACTIVE_CIS_CONDITIONS
            ).values_list(
                'child__id',
                flat=True
            ),
            parent__type_id=CI_TYPES.PROFIT_CENTER,
            child__type_id=CI_TYPES.SERVICE,
            type=CI_RELATION_TYPES.CONTAINS,
            **ACTIVE_CIS_CONDITIONS
        )
        if self.calc_in_scrooge_cis:
            query = query.filter(child__id__in=self.calc_in_scrooge_cis)
        services_ids.update(set(query.values_list('child__id', flat=True)))
        return services_ids

    def get_queryset(self):
        queryset = Device.objects.all()
        if self.environment_id:
            queryset = queryset.filter(
                device_environment_id=self.environment_id
            )
        if self.service_id:
            queryset = queryset.filter(
                service_id=self.service_id
            )
        if self.businessline_id:
            queryset = queryset.filter(
                service_id__in=self._get_businessline_services_ids(
                    self.businessline_id
                )
            )
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


class ReportServicesDeviceList(ReportDeviceList, ServicesDeviceList):
    pass
