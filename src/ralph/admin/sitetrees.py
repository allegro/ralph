# -*- coding: utf-8 -*-
from django.apps import apps
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
    # permission is created in '<app>.{add|change|view}_<model>' format
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
                '{}.view_{}'.format(app, model),
            ])
        elif hasattr(child, 'permissions'):
            access_by_perms.extend(child.permissions)
    if access_by_perms:
        kwargs['access_by_perms'] = list(set(access_by_perms))
    return item(*args, **kwargs)


extra_views = ralph_site.get_extra_view_menu_items()


def get_menu_items_for_admin(name, perm):
    # TODO: detailed permissions for extra views
    return [
        ralph_item(access_by_perms=perm, **view)
        for view in extra_views[name]
    ]


def section(section_name, app, model):
    app, model = map(str.lower, [app, model])
    model_class = apps.get_model(app, model)
    # support for proxy model beacause this bug
    # https://code.djangoproject.com/ticket/11154
    change_perm = '{}.change_{}'.format(app, model)
    item = ralph_item(
        title=section_name,
        url='admin:{}_{}_changelist'.format(app, model),
        access_by_perms='{}.view_{}'.format(app, model),
        perms_mode_all=False,
        children=[
            ralph_item(
                title=_('Add {}'.format(
                    model_class._meta.verbose_name.lower()
                )),
                url='admin:{}_{}_add'.format(app, model),
                access_by_perms='{}.add_{}'.format(app, model),
            ),
            ralph_item(
                title='{{ original }}',
                url='admin:{}_{}_change original.id'.format(app, model),
                access_by_perms=change_perm,
                children=get_menu_items_for_admin(
                    '{}_{}'.format(app, model),
                    change_perm,
                ),
            ),
        ]
    )
    # save app and model info to create permissions entries later
    item._app = app
    item._model = model
    return item

cross_validation_items = []
if settings.RALPH2_RALPH3_CROSS_VALIDATION_ENABLED:
    cross_validation_items = [
        section(
            _('Ralph2 Validation'), 'cross_validator', 'CrossValidationRun'
        ),
    ]

sitetrees = [
    tree('ralph_admin', items=[
        ralph_item(
            title=_('Data Center'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('All hosts'), 'data_center', 'DCHost'),
                ralph_item(
                    title=_('DC Visualization'),
                    url='dc_view',
                    access_by_perms='accounts.can_view_extra_serverroomview'
                ),
                section(_('Hardware'), 'data_center', 'DataCenterAsset'),
                section(_('Virtual Servers'), 'virtual', 'VirtualServer'),
                section(_('Clusters'), 'data_center', 'cluster'),
                section(_('Cloud hosts'), 'virtual', 'CloudHost'),
                section(_('Cloud projects'), 'virtual', 'CloudProject'),
                section(_('Data Centers'), 'data_center', 'DataCenter'),
                section(_('Racks'), 'data_center', 'Rack'),
                section(_('Rack Accessories'), 'data_center', 'RackAccessory'),
                section(_('Accessories'), 'data_center', 'Accessory'),
                section(_('Databases'), 'data_center', 'Database'),
                section(_('Disk Shares'), 'data_center', 'DiskShare'),
                section(_('Server Rooms'), 'data_center', 'ServerRoom'),
                section(_('VIPs'), 'data_center', 'VIP'),
                section(_('Preboots'), 'deployment', 'Preboot'),
                section(
                    _('Preboot configuration'), 'deployment',
                    'PrebootConfiguration'
                ),
                section(_('Preboot files'), 'deployment', 'PrebootFile'),
            ],
        ),
        ralph_item(
            title=_('Back Office'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Hardware'), 'back_office', 'backofficeasset'),
                section(_('Warehouses'), 'back_office', 'warehouse'),
                section(
                    _('Office Infrastructures'),
                    'back_office',
                    'officeinfrastructure'
                ),
            ]
        ),
        ralph_item(
            title=_('Networks'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Networks'), 'networks', 'network'),
                section(
                    _('Network environments'), 'networks', 'networkenvironment'
                ),
                section(_('Network kind'), 'networks', 'networkkind'),
                section(_('IP Addresses'), 'networks', 'ipaddress'),
                section(_('DHCP Servers'), 'dhcp', 'DHCPServer'),
                section(_('DNS Servers'), 'dhcp', 'DNSServer'),
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
                section(_('Software'), 'licences', 'Software'),
            ]
        ),
        ralph_item(
            title=_('Domains'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Domains'), 'domains', 'Domain'),
                section(_('Contracts'), 'domains', 'DomainContract'),
                section(_('Registrants'), 'domains', 'DomainRegistrant'),
                section(_('Owners'), 'accounts', 'RalphUser'),
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
                section(_('Assets supports'), 'supports', 'BaseObjectsSupport'),
            ]
        ),
        ralph_item(
            title=_('Reports'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                ralph_item(
                    title=_('Category model'),
                    url='category_model_report',
                    access_by_perms=(
                        'accounts.can_view_extra_categorymodelreport'
                    ),
                ),
                ralph_item(
                    title=_('Category model status'),
                    url='category_model__status_report',
                    access_by_perms=(
                        'accounts.can_view_extra_categorymodelstatusreport'
                    ),
                ),
                ralph_item(
                    title=_('Manufacturer category model'),
                    url='manufactured_category_model_report',
                    access_by_perms=(
                        'accounts.'
                        'can_view_extra_manufacturercategorymodelreport'
                    ),
                ),
                ralph_item(
                    title=_('Status model'),
                    url='status_model_report',
                    access_by_perms=(
                        'accounts.can_view_extra_statusmodelreport'
                    ),
                ),
                ralph_item(
                    title=_('Asset - relations'),
                    url='asset-relations',
                    access_by_perms=(
                        'accounts.can_view_extra_assetrelationsreport'
                    ),
                ),
                ralph_item(
                    title=_('Licence - relations'),
                    url='licence-relations',
                    access_by_perms=(
                        'accounts.can_view_extra_licencerelationsreport'
                    ),
                ),
                ralph_item(
                    title=_('Assets - supports'),
                    url='assets-supports',
                    access_by_perms=(
                        'accounts.can_view_extra_assetsupportsreport'
                    ),
                ),
                ralph_item(
                    title=_('Failures'),
                    url='failures-report',
                    access_by_perms=(
                        'accounts.can_view_extra_failurereport'
                    ),
                ),
            ]
        ),
        ralph_item(
            title=_('Operations'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Changes'), 'operations', 'Change'),
                section(_('Problems'), 'operations', 'Problem'),
                section(_('Incidents'), 'operations', 'Incident'),
                section(_('Failures'), 'operations', 'Failure'),
                section(_('All'), 'operations', 'Operation'),
                section(_('Types'), 'operations', 'OperationType'),
            ]
        ),
        ralph_item(
            title=_('Dashboards'),
            url='#',
            url_as_pattern=False,
            perms_mode_all=False,
            children=[
                section(_('Dashboards'), 'dashboards', 'Dashboard'),
                section(_('Graphs'), 'dashboards', 'Graph'),
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
                section(_('Business segment'), 'assets', 'BusinessSegment'),
                section(_('Profit center'), 'assets', 'ProfitCenter'),
                section(_('Service'), 'assets', 'Service'),
                section(_('Environment'), 'assets', 'Environment'),
                section(_('Budget info'), 'assets', 'BudgetInfo'),
                section(
                    _('Service Environment'), 'assets', 'ServiceEnvironment'
                ),
                section(
                    _('Configuration modules'), 'assets', 'ConfigurationModule'
                ),
                section(
                    _('Configuration classes'), 'assets', 'ConfigurationClass'
                ),
                section(_('Asset holder'), 'assets', 'AssetHolder'),
                section(_('Users list'), 'accounts', 'RalphUser'),
                section(_('Groups list'), 'auth', 'Group'),
                section(_('Regions'), 'accounts', 'Region'),
                section(_('Transitions'), 'transitions', 'TransitionModel'),
                section(_('Report template'), 'reports', 'Report'),
                section(_('Custom fields'), 'custom_fields', 'CustomField'),
            ] + cross_validation_items
        )
    ])
]

register_i18n_trees(['ralph_admin'])
