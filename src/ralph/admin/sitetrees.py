# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate

from sitetree.sitetreeapp import register_i18n_trees
from sitetree.utils import (
    tree,
    item
)

# To generate and display the menu, use the command:
# ralph sitetreeload
# ralph sitetree_resync_apps

activate(settings.LANGUAGE_CODE)

sitetrees = (
    tree('ralph_admin', items=[
        item(
            _('Data Center'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'data_center.change_datacenterasset',
                'data_center.change_cloudproject',
                'data_center.change_datacenter',
                'data_center.change_database',
                'data_center.change_diskshare',
                'data_center.change_rackaccessory',
                'data_center.change_serverroom',
                'data_center.change_vip',
                'data_center.change_virtualserver'
            ],
            perms_mode_all=False,
            children=[
                item(
                    title=_('Hardware'),
                    url='admin:data_center_datacenterasset_changelist',
                    access_by_perms='data_center.change_datacenterasset'
                ),
                item(
                    title=_('Cloud projects'),
                    url='admin:data_center_cloudproject_changelist',
                    access_by_perms='data_center.change_cloudproject'
                ),
                item(
                    title=_('Data Centers'),
                    url='admin:data_center_datacenter_changelist',
                    access_by_perms='data_center.change_datacenter'
                ),
                item(
                    title=_('Databases'),
                    url='admin:data_center_database_changelist',
                    access_by_perms='data_center.change_database'
                ),
                item(
                    title=_('DiskShares'),
                    url='admin:data_center_diskshare_changelist',
                    access_by_perms='data_center.change_diskshare'
                ),
                item(
                    title=_('Rack Accessories'),
                    url='admin:data_center_rackaccessory_changelist',
                    access_by_perms='data_center.change_rackaccessory'
                ),
                item(
                    title=_('Server Rooms'),
                    url='admin:data_center_serverroom_changelist',
                    access_by_perms='data_center.change_serverroom'
                ),
                item(
                    title=_('VIPs'),
                    url='admin:data_center_vip_changelist',
                    access_by_perms='data_center.change_vip'
                ),
                item(
                    title=_('Virtual Servers'),
                    url='admin:data_center_virtualserver_changelist',
                    access_by_perms='data_center.change_virtualserver'
                ),
            ]
        ),
        item(
            _('DC Visualization'),
            url='dc_view',
            access_by_perms=''  # TODO add permissions
        ),
        item(
            _('Racks'),
            url='admin:data_center_rack_changelist',
            access_by_perms='data_center.change_rack'
        ),
        item(
            _('Back Office'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'back_office.change_backofficeasset',
                'back_office.change_warehouse'
            ],
            perms_mode_all=False,
            children=[
                item(
                    title=_('Hardware'),
                    url='admin:back_office_backofficeasset_changelist',
                    access_by_perms='back_office.change_backofficeasset'
                ),
                item(
                    title=_('Warehouses'),
                    url='admin:back_office_warehouse_changelist',
                    access_by_perms='back_office.change_warehouse'
                ),
            ]
        ),
        item(
            _('Licenses'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'licences.change_licence',
                'licences.change_licencetype',
                'licences.change_softwarecategory'
            ],
            perms_mode_all=False,
            children=[
                item(
                    title=_('All'),
                    url='admin:licences_licence_changelist',
                    access_by_perms='licences.change_licence'
                ),
                item(
                    title=_('Types'),
                    url='admin:licences_licencetype_changelist',
                    access_by_perms='licences.change_licencetype'
                ),
                item(
                    title=_('Categories'),
                    url='admin:licences_softwarecategory_changelist',
                    access_by_perms='licences.change_softwarecategory'
                ),
            ]
        ),
        item(
            _('Supports'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'supports.change_support',
                'supports.change_supporttype'
            ],
            perms_mode_all=False,
            children=[
                item(
                    title=_('All'),
                    url='admin:supports_support_changelist',
                    access_by_perms='supports.change_support'
                ),
                item(
                    title=_('Types'),
                    url='admin:supports_supporttype_changelist',
                    access_by_perms='supports.change_supporttype'
                ),
            ]
        ),
        item(
            _('Settings'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'auth.change_user', 'auth.add_user',
                'auth.change_group', 'auth.add_group'
            ],
            perms_mode_all=False,
            children=[
                item(
                    title=_('Asset model'),
                    url='admin:assets_assetmodel_changelist',
                    access_by_perms='assets.change_assetmodel',
                ),
                item(
                    title=_('Manufacturer'),
                    url='admin:assets_manufacturer_changelist',
                    access_by_perms='assets.change_manufacturer',
                ),
                item(
                    title=_('Service'),
                    url='admin:assets_service_changelist',
                    access_by_perms='assets.change_service',
                ),
                item(
                    title=_('Environment'),
                    url='admin:assets_environment_changelist',
                    access_by_perms='assets.change_environment',
                ),
                item(
                    title=_('Service Environment'),
                    url='admin:assets_serviceenvironment_changelist',
                    access_by_perms='assets.change_serviceenvironment',
                ),
                item(
                    title=_('Users list'),
                    url='admin:auth_user_changelist',
                    access_by_perms='auth.change_user',
                ),
                item(
                    title=_('Add user'),
                    url='admin:auth_user_add',
                    access_by_perms='auth.add_user',
                ),
                item(
                    title=_('Groups list'),
                    url='admin:auth_group_changelist',
                    access_by_perms='auth.change_group',
                ),
                item(
                    title=_('Add group'),
                    url='admin:auth_group_add',
                    access_by_perms='auth.add_group',
                ),
            ]
        ),
    ]),
)

register_i18n_trees(['ralph_admin'])
