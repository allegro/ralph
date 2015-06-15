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


def ralph_item(*args, **kwargs):
    kwargs.setdefault('access_loggedin', True)
    return item(*args, **kwargs)


sitetrees = (
    tree('ralph_admin', items=[
        ralph_item(
            title=_('Data Center'),
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
                ralph_item(
                    title=_('Hardware'),
                    url='admin:data_center_datacenterasset_changelist',
                    access_by_perms='data_center.change_datacenterasset'
                ),
                ralph_item(
                    title=_('Cloud projects'),
                    url='admin:data_center_cloudproject_changelist',
                    access_by_perms='data_center.change_cloudproject'
                ),
                ralph_item(
                    title=_('Data Centers'),
                    url='admin:data_center_datacenter_changelist',
                    access_by_perms='data_center.change_datacenter'
                ),
                ralph_item(
                    title=_('Databases'),
                    url='admin:data_center_database_changelist',
                    access_by_perms='data_center.change_database'
                ),
                ralph_item(
                    title=_('DiskShares'),
                    url='admin:data_center_diskshare_changelist',
                    access_by_perms='data_center.change_diskshare'
                ),
                ralph_item(
                    title=_('Rack Accessories'),
                    url='admin:data_center_rackaccessory_changelist',
                    access_by_perms='data_center.change_rackaccessory'
                ),
                ralph_item(
                    title=_('Server Rooms'),
                    url='admin:data_center_serverroom_changelist',
                    access_by_perms='data_center.change_serverroom'
                ),
                ralph_item(
                    title=_('VIPs'),
                    url='admin:data_center_vip_changelist',
                    access_by_perms='data_center.change_vip'
                ),
                ralph_item(
                    title=_('Virtual Servers'),
                    url='admin:data_center_virtualserver_changelist',
                    access_by_perms='data_center.change_virtualserver'
                ),
            ]
        ),
        ralph_item(
            title=_('DC Visualization'),
            url='dc_view',
            access_by_perms=''  # TODO add permissions
        ),
        ralph_item(
            title=_('Racks'),
            url='admin:data_center_rack_changelist',
            access_by_perms='data_center.change_rack'
        ),
        ralph_item(
            title=_('Back Office'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'back_office.change_backofficeasset',
                'back_office.change_warehouse',
            ],
            perms_mode_all=False,
            children=[
                ralph_item(
                    title=_('Hardware'),
                    url='admin:back_office_backofficeasset_changelist',
                    access_by_perms='back_office.change_backofficeasset'
                ),
                ralph_item(
                    title=_('Warehouses'),
                    url='admin:back_office_warehouse_changelist',
                    access_by_perms='back_office.change_warehouse'
                ),
            ]
        ),
        ralph_item(
            title=_('Licenses'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'licences.change_licence',
                'licences.change_licencetype',
                'licences.change_softwarecategory'
            ],
            perms_mode_all=False,
            children=[
                ralph_item(
                    title=_('All'),
                    url='admin:licences_licence_changelist',
                    access_by_perms='licences.change_licence'
                ),
                ralph_item(
                    title=_('Types'),
                    url='admin:licences_licencetype_changelist',
                    access_by_perms='licences.change_licencetype'
                ),
                ralph_item(
                    title=_('Categories'),
                    url='admin:licences_softwarecategory_changelist',
                    access_by_perms='licences.change_softwarecategory'
                ),
            ]
        ),
        ralph_item(
            title=_('Supports'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'supports.change_support',
                'supports.change_supporttype'
            ],
            perms_mode_all=False,
            children=[
                ralph_item(
                    title=_('All'),
                    url='admin:supports_support_changelist',
                    access_by_perms='supports.change_support'
                ),
                ralph_item(
                    title=_('Types'),
                    url='admin:supports_supporttype_changelist',
                    access_by_perms='supports.change_supporttype'
                ),
            ]
        ),
        ralph_item(
            title=_('Settings'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'auth.change_user', 'auth.add_user',
                'auth.change_group', 'auth.add_group'
            ],
            perms_mode_all=False,
            children=[
                ralph_item(
                    title=_('Asset model'),
                    url='admin:assets_assetmodel_changelist',
                    access_by_perms='assets.change_assetmodel'
                ),
                ralph_item(
                    title=_('Manufacturer'),
                    url='admin:assets_manufacturer_changelist',
                    access_by_perms='assets.change_manufacturer'
                ),
                ralph_item(
                    title=_('Service'),
                    url='admin:assets_service_changelist',
                    access_by_perms='assets.change_service'
                ),
                ralph_item(
                    title=_('Environment'),
                    url='admin:assets_environment_changelist',
                    access_by_perms='assets.change_environment'
                ),
                ralph_item(
                    title=_('Service Environment'),
                    url='admin:assets_serviceenvironment_changelist',
                    access_by_perms='assets.change_serviceenvironment'
                ),
                ralph_item(
                    title=_('Users list'),
                    url='admin:auth_user_changelist',
                    access_by_perms='auth.change_user'
                ),
                ralph_item(
                    title=_('Add user'),
                    url='admin:auth_user_add',
                    access_by_perms='auth.add_user'
                ),
                ralph_item(
                    title=_('Groups list'),
                    url='admin:auth_group_changelist',
                    access_by_perms='auth.change_group'
                ),
                ralph_item(
                    title=_('Add group'),
                    url='admin:auth_group_add',
                    access_by_perms='auth.add_group'
                ),
            ]
        ),
    ]),
)

register_i18n_trees(['ralph_admin'])
