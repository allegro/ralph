# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate

from sitetree.sitetreeapp import register_i18n_trees
from sitetree.utils import (
    tree,
    item
)

from ralph.admin.sites import ralph_site
# To generate and display the menu, use the command:
# ralph sitetreeload
# ralph sitetree_resync_apps

activate(settings.LANGUAGE_CODE)


def ralph_item(*args, **kwargs):
    kwargs.setdefault('access_loggedin', True)
    return item(*args, **kwargs)


extra_views = ralph_site.get_extra_view_menu_items()


def get_menu_items_for_admin(name):
    return [
        ralph_item(
            access_by_perms='data_center.change_datacenterasset', **view)
        for view in extra_views[name]
    ]


def section(section_name, app, model):
    app, model = map(str.lower, [app, model])
    return ralph_item(
        title=section_name,
        url='admin:{}_{}_changelist'.format(app, model),
        access_by_perms='{}.change_{}'.format(app, model),
        children=[
            ralph_item(
                title=_('Add'),
                url='admin:{}_{}_add'.format(app, model),
                access_by_perms='{}.add_{}'.format(app, model),
            ),
            ralph_item(
                title='{{ original }}',
                url='admin:{}_{}_change original.id'.format(app, model),
                access_by_perms='{}.change_{}'.format(app, model),
                children=get_menu_items_for_admin(
                    '{}_{}'.format(app, model)
                ),
            ),
        ]
    )


sitetrees = [
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
                section(_('Hardware'), 'data_center', 'DataCenterAsset'),
                section(_('Cloud projects'), 'data_center', 'CloudProject'),
                section(_('Data Centers'), 'data_center', 'DataCenter'),
                section(_('Databases'), 'data_center', 'Database'),
                section(_('Disk Shares'), 'data_center', 'DiskShare'),
                section(_('Data Centers'), 'data_center', 'DataCenter'),
                section(_('Rack Accessories'), 'data_center', 'RackAccessory'),
                section(_('Server Rooms'), 'data_center', 'ServerRoom'),
                section(_('VIPs'), 'data_center', 'VIP'),
                section(_('Data Centers'), 'data_center', 'DataCenter'),
                section(_('Virtual Servers'), 'data_center', 'VirtualServer'),
                section(_('IP Addresses'), 'data_center', 'ipaddress'),
            ],
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
                section(_('Hardware'), 'back_office', 'backofficeasset'),
                section(_('Warehouses'), 'back_office', 'warehouse'),
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
                section(_('Licences'), 'licences', 'Licence'),
                section(_('Types'), 'licences', 'LicenceType'),
                section(_('Categories'), 'licences', 'SoftwareCategory'),
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
                section(_('Supports'), 'supports', 'Support'),
                section(_('Types'), 'supports', 'SupportType'),
            ]
        ),
        ralph_item(
            title=_('Settings'),
            url='#',
            url_as_pattern=False,
            access_by_perms=[
                'accounts.change_ralphuser', 'accounts.add_ralphuser',
                'auth.change_group', 'auth.add_group'
            ],
            perms_mode_all=False,
            children=[
                section(_('Asset model'), 'assets', 'AssetModel'),
                section(_('Manufacturer'), 'assets', 'Manufacturer'),
                section(_('Service'), 'assets', 'Service'),
                section(_('Environment'), 'assets', 'Environment'),
                section(
                    _('Service Environment'), 'assets', 'ServiceEnvironment'
                ),
                section(_('Users list'), 'accounts', 'RalphUser'),
                section(_('Groups list'), 'auth', 'Group'),
            ]
        )
    ])
]

register_i18n_trees(['ralph_admin'])
