# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.menu import MenuItem

from ralph.cmdb.models_ci import CILayer
from ralph.menu import Menu


class CMDBMenu(Menu):
    module = MenuItem(
        'CMDB',
        name='module_cmdb',
        fugue_icon='fugue-thermometer',
        href='/cmdb/changes/timeline',
    )

    def get_submodules(self):
        return [
            MenuItem(
                'Configuration items',
                name='configuration_items',
                fugue_icon='fugue-block',
                view_name='cmdb_timeline',
            ),
            MenuItem(
                'CI by layers',
                name='layers',
                fugue_icon='fugue-applications-blue',
                href='/cmdb/search',
            ),
            MenuItem(
                'Reports',
                name='ci_reports',
                fugue_icon='fugue-reports',
                href='/cmdb/changes/reports?kind=top_changes',
            ),
            MenuItem(
                'Events and changes',
                name='events',
                fugue_icon='fugue-arrow-circle-double',
                href='/cmdb/changes/changes',
            ),
            MenuItem(
                'Others',
                name='ci_others',
                fugue_icon='fugue-beaker',
                href='/cmdb/archive/assets/',
            ),
        ]

    def get_sidebar_items(self):

        def generate_menu_items(data):
            return [
                MenuItem(
                    label=t[1],
                    fugue_icon=t[2],
                    href=t[0],
                ) for t in data]

        ci = (
            ('/cmdb/add', 'Add CI', 'fugue-block--plus'),
            ('/cmdb/changes/dashboard', 'Dashboard', 'fugue-dashboard'),
            ('/cmdb/graphs', 'Impact report', 'fugue-dashboard'),
            ('/cmdb/changes/timeline', 'Timeline View', 'fugue-dashboard'),
            ('/admin/cmdb', 'Admin', 'fugue-toolbox'),
            ('/cmdb/cleanup', 'Clean up', 'fugue-broom'),
        )
        reports = (
            ('/cmdb/changes/reports?kind=top_changes',
                'Top CI changes', 'fugue-reports'),
            ('/cmdb/changes/reports?kind=top_problems',
                'Top CI problems', 'fugue-reports'),
            ('/cmdb/changes/reports?kind=top_incidents',
                'Top CI incidents', 'fugue-reports'),
            ('/cmdb/changes/reports?kind=usage',
                'Cis w/o changes', 'fugue-reports'),
        )
        events = (
            ('/cmdb/changes/changes', 'All Events', 'fugue-arrow'),
            ('/cmdb/changes/changes?type=3', 'Asset attr. changes',
                'fugue-wooden-box--arrow'),
            ('/cmdb/changes/changes?type=4', 'Monitoring events',
                'fugue-thermometer'),
            ('/cmdb/changes/changes?type=1', 'Repo changes',
                'fugue-git'),
            ('/cmdb/changes/changes?type=2', 'Agent events',
                'fugue-flask'),
            ('/cmdb/changes/incidents', 'Incidents',
                'fugue-question'),
            ('/cmdb/changes/problems', 'Problems',
                'fugue-bomb'),
            ('/cmdb/changes/jira_changes', 'Jira Changes',
                'fugue-arrow-retweet'),
        )
        layers = (
            ('/cmdb/search', 'All Cis (all layers)', 'fugue-magnifier'),
        )
        layers += tuple([(
            '/cmdb/search?layer=%d' % layer.id,
            layer.name,
            layer.icon.raw if layer.icon else 'fugue-layers-stack-arrange',
        ) for layer in CILayer.objects.order_by('name')])

        others = (
            ('/cmdb/archive/assets/', 'Asset attr. changes',
             'fugue-wooden-box--arrow'),
            ('/cmdb/archive/cmdb/', 'CI attributes changes',
                'fugue-puzzle',),
            ('/cmdb/archive/zabbix/', 'Monitoring events',
                'fugue-thermometer',),
            ('/cmdb/archive/git/', 'Repo changes',
                'fugue-git',),
            ('/cmdb/archive/puppet/', 'Agent events',
                'fugue-flask',),
        )
        return {
            'configuration_items': generate_menu_items(ci),
            'events': generate_menu_items(events),
            'ci_reports': generate_menu_items(reports),
            'layers': generate_menu_items(layers),
            'ci_others': generate_menu_items(others),
        }

menu_class = CMDBMenu
