# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _


ADMIN_MENU = (
    {
        'label': _('DC Assets'),
        'url': None,
        'sub_menu': (
            {
                'label': _('All'),
                'url': reverse_lazy(
                    'admin:data_center_datacenterasset_changelist'
                )
            },
            {
                'label': _('Cloud projects'),
                'url': reverse_lazy(
                    'admin:data_center_cloudproject_changelist'
                )
            },
            {
                'label': _('Data Centers'),
                'url': reverse_lazy(
                    'admin:data_center_datacenter_changelist'
                )
            },
            {
                'label': _('Databases'),
                'url': reverse_lazy(
                    'admin:data_center_database_changelist'
                )
            },
            {
                'label': _('DiskShares'),
                'url': reverse_lazy(
                    'admin:data_center_diskshare_changelist'
                )
            },
            {
                'label': _('Rack Accessories'),
                'url': reverse_lazy(
                    'admin:data_center_rackaccessory_changelist'
                )
            },
            {
                'label': _('Server Rooms'),
                'url': reverse_lazy(
                    'admin:data_center_serverroom_changelist'
                )
            },
            {
                'label': _('VIPs'),
                'url': reverse_lazy(
                    'admin:data_center_vip_changelist'
                )
            },
            {
                'label': _('Virtual Servers'),
                'url': reverse_lazy(
                    'admin:data_center_virtualserver_changelist'
                )
            },
        )
    },
    {
        'label': _('DC Visualization'),
        'url': None,
        'sub_menu': None
    },
    {
        'label': _('Racks'),
        'url': reverse_lazy(
            'admin:data_center_rack_changelist'
        ),
        'sub_menu': None
    },
    {
        'label': _('BO Assets'),
        'url': None,
        'sub_menu': (
            {
                'label': _('All'),
                'url': reverse_lazy(
                    'admin:back_office_backofficeasset_changelist'
                )
            },
            {
                'label': _('Warehouses'),
                'url': reverse_lazy(
                    'admin:back_office_warehouse_changelist'
                )
            },
        )
    },
    {
        'label': _('Licenses'),
        'url': None,
        'sub_menu': (
            {
                'label': _('All'),
                'url': reverse_lazy(
                    'admin:licences_licence_changelist'
                )
            },
            {
                'label': _('Types'),
                'url': reverse_lazy(
                    'admin:licences_licencetype_changelist'
                )
            },
            {
                'label': _('Categories'),
                'url': reverse_lazy(
                    'admin:licences_softwarecategory_changelist'
                )
            },
        )
    },
    {
        'label': _('Supports'),
        'url': None,
        'sub_menu': (
            {
                'label': _('All'),
                'url': reverse_lazy(
                    'admin:supports_support_changelist'
                )
            },
            {
                'label': _('Types'),
                'url': reverse_lazy(
                    'admin:supports_supporttype_changelist'
                )
            },
        )
    },
    {
        'label': _('Settings'),
        'url': None,
        'sub_menu': (
            {
                'separate_label': 'Users settings',
                'label': _('Users list'),
                'url': reverse_lazy('admin:auth_user_changelist'),
            },
            {
                'label': _('Add user'),
                'url': reverse_lazy('admin:auth_user_add')
            },
            {
                'separate_label': 'Groups settings',
                'label': _('Groups list'),
                'url': reverse_lazy('admin:auth_group_changelist')
            },
            {
                'label': _('Add group'),
                'url': reverse_lazy('admin:auth_group_add')
            },
        )
    },
)
