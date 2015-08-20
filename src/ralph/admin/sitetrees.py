# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate
from sitetree.sitetreeapp import register_i18n_trees
from sitetree.utils import item, tree

from ralph.admin.sites import ralph_site

# To generate and display the menu, use the command:
# ralph sitetreeload
# ralph sitetree_resync_apps

activate(settings.LANGUAGE_CODE)


def ralph_item(*args, **kwargs):
    kwargs.setdefault('access_loggedin', True)

    # create access_by_perms entries by iterating through all children
    # and extracting app and model name from it
    # permission is created in '<app>.{add|change}_<model>' format
    access_by_perms = kwargs.get('access_by_perms', [])
    if isinstance(access_by_perms, (str, int)):
        access_by_perms = [access_by_perms]
    for child in kwargs.get('children', []):
        if hasattr(child, '_model') and hasattr(child, '_app'):
            model = child._model.lower()
            app = child._app.lower()
            access_by_perms.extend([
                '{}.add_{}'.format(app, model),
                '{}.change_{}'.format(app, model),
            ])
    if access_by_perms:
        kwargs['access_by_perms'] = list(set(access_by_perms))
    return item(*args, **kwargs)


extra_views = ralph_site.get_extra_view_menu_items()


def get_menu_items_for_admin(name, perm):
    # TODO: detailed permissions for extra views
    return [
        ralph_item(access_by_perms=perm, **view) for view in extra_views[name]
    ]


def section(section_name, app, model):
    app, model = map(str.lower, [app, model])
    change_perm = '{}.change_{}'.format(app, model)
    item = ralph_item(
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
                access_by_perms=change_perm,
                children=get_menu_items_for_admin(
                    '{}_{}'.format(app, model),
                    change_perm
                ),
            ),
        ]
    )
    # save app and model info to create permissions entries later
    item._app = app
    item._model = model
    return item

sitetrees = [
    tree('ralph_admin', items=[
        ralph_item(
            title=_('Data Center'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Hardware'), 'data_center', 'DataCenterAsset'),
                section(_('Racks'), 'data_center', 'Rack'),
                section(_('Cloud projects'), 'data_center', 'CloudProject'),
                section(_('Data Centers'), 'data_center', 'DataCenter'),
                section(_('Databases'), 'data_center', 'Database'),
                section(_('Disk Shares'), 'data_center', 'DiskShare'),
                section(_('Rack Accessories'), 'data_center', 'RackAccessory'),
                section(_('Server Rooms'), 'data_center', 'ServerRoom'),
                section(_('VIPs'), 'data_center', 'VIP'),
                section(_('Virtual Servers'), 'data_center', 'VirtualServer'),
                section(_('IP Addresses'), 'data_center', 'ipaddress'),
            ],
        ),
        ralph_item(
            title=_('DC Visualization'),
            url='dc_view',
            # TODO add permissions
        ),
        ralph_item(
            title=_('Back Office'),
            url='#',
            url_as_pattern=False,
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
            perms_mode_all=False,
            children=[
                section(_('Supports'), 'supports', 'Support'),
                section(_('Types'), 'supports', 'SupportType'),
            ]
        ),
        ralph_item(
            title=_('Reports'),
            url='#',
            children=[
                ralph_item(
                    title=_('Category model'),
                    url='category_model_report',
                ),
                ralph_item(
                    title=_('Category model status'),
                    url='category_model__status_report',
                ),
                ralph_item(
                    title=_('Manufacturer category model'),
                    url='manufactured_category_model_report',
                ),
                ralph_item(
                    title=_('Status model'),
                    url='status_model_report',
                ),
            ]
        ),
        ralph_item(
            title=_('Settings'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Asset model'), 'assets', 'AssetModel'),
                section(_('Asset category'), 'assets', 'Category'),
                section(_('Manufacturer'), 'assets', 'Manufacturer'),
                section(_('Service'), 'assets', 'Service'),
                section(_('Environment'), 'assets', 'Environment'),
                section(
                    _('Service Environment'), 'assets', 'ServiceEnvironment'
                ),
                section(_('Users list'), 'accounts', 'RalphUser'),
                section(_('Groups list'), 'auth', 'Group'),
                section(_('Regions'), 'accounts', 'Region'),
            ]
        )
    ])
]

register_i18n_trees(['ralph_admin'])
