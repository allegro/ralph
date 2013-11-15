# -*- coding: utf-8 -*-

"""
Scan results merger.

It merges results from all available plugins with data stored in the database.
The main idea of this merger is to use all possible unique keys for merged
component. It's similar to DB `unique` and `unique together` keys.
E.g.:
1. For disks will be:
    - serial_number
    - device, mount_point
2. For fibrechannel cards will be:
    - device, physical_id

The same idea is used when we try to make a diff.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.conf import settings


logger = logging.getLogger("SCAN")


def _get_results_priority(plugin, component):
    try:
        return settings.SCAN_PLUGINS[plugin]['results_priority'][component]
    except KeyError:
        logger.warning(
            "Result priority for plugin '%s' and component '%s' not found." % (
                plugin,
                component,
            ),
        )
        return 1


def _get_ranked_plugins_list(plugins, component):
    return [
        item['plugin'] for item in sorted(
            [
                {
                    'plugin': plugin,
                    'priority': _get_results_priority(plugin, component),
                } for plugin in plugins
            ],
            key=lambda k: k['priority'],
        )
    ]


def _find_data(rows, lookup):
    for row in rows:
        matched = True
        for field, value in lookup.iteritems():
            if (
                field not in row or
                not str(row[field]) or
                str(value).strip().lower() != str(row[field]).strip().lower()
            ):
                matched = False
                break
        if matched:
            return row


def merge(component, data, unique_fields, db_plugin_name='database'):
    """
    Merge data for component based on unique fields set.

    :param component: component with we act
    :param data: results from plugins
    :param unique_fields: set of unique or unique_together fields for component
    :param db_plugin_name: name of plugin which includes data from the
                           database
    """

    # First we are creating data structure which contains only dicts (rows)
    # that have keys from unique_fields param.
    # We store this data in tricky way. We want easy find dict by
    # unique_fields - this is the main idea.
    # E.g.:
    # Input:
    # unique_fiels = [('serial_number',), ('device', 'mount_point')]
    # data = {
    #     'disks': [
    #         {
    #             'serial_number': 'sn 1',
    #             'param_1': 'value 1',
    #         },
    #         {
    #             'device': '100',
    #             'param_2': 'value 2',
    #         },
    #         {
    #             'device': '101',
    #             'mount_point': '/dev/sda',
    #             'param_1': 'value 1',
    #         },
    #         {
    #             'device': '102',
    #             'mount_point': '/dev/sdb',
    #             'serial_number': 'sn 2',
    #             'param_2': 'value 2',
    #         },
    #     ],
    # }
    #
    # Output:
    # usefull_data == {
    #     'disks': {
    #         ('serial_number',): [
    #             {
    #                 'serial_number': 'sn 1',
    #                 'param_1': 'value 1',
    #             },
    #             {
    #                 'device': '102',
    #                 'mount_point': '/dev/sdb',
    #                 'serial_number': 'sn 2',
    #                 'param_2': 'value 2',
    #             },
    #         ],
    #         ('device', 'mount_point'): [
    #             {
    #                 'device': '101',
    #                 'mount_point': '/dev/sda',
    #                 'param_1': 'value 1',
    #             },
    #             {
    #                 'device': '102',
    #                 'mount_pount': '/dev/sdb',
    #                 'serial_number': 'sn 2',
    #                 'param_2': 'value 2',
    #             },
    #         ]
    #     },
    # }
    usefull_data = {}
    for plugin, plugin_results in data.iteritems():
        for row in plugin_results:
            for unique_group in unique_fields:
                fields = set([
                    field for field in unique_group
                    if unicode(row.get(field, ''))
                ])
                if set(unique_group) == fields:
                    if plugin not in usefull_data:
                        usefull_data[plugin] = {}
                    if unique_group not in usefull_data[plugin]:
                        usefull_data[plugin][unique_group] = []
                    usefull_data[plugin][unique_group].append(row)
    plugins = usefull_data.keys()  # use only usefull plugins
    try:
        plugins.remove(db_plugin_name)
    except ValueError:
        pass
    ranked_plugins = _get_ranked_plugins_list(plugins, component)  # rank it
    if db_plugin_name in data:
        ranked_plugins.append(db_plugin_name)  # add db plugin on the end
    merged_data = []
    for plugin in ranked_plugins:
        groups = usefull_data.get(plugin, {}).keys()  # get only usefull groups
                                                      # of unique fields for
                                                      # plugin
        for unique_group in groups:
            for new_row in usefull_data[plugin][unique_group]:
                lookup = {}
                for field in unique_group:
                    lookup[field] = new_row[field]
                # find previous version of this dict (row) by current lookup
                current_row = _find_data(merged_data, lookup)
                if current_row:
                    # now we should update it or complete values that are
                    # only in the database
                    if plugin == db_plugin_name:
                        for field, value in new_row.iteritems():
                            if not current_row.get(field):
                                current_row[field] = value
                    else:
                        current_row.update(new_row)
                else:
                    # in this case dict could be in merged_data - but current
                    # lookup can't find it - we must try other
                    # possible lookups
                    exists_in_results = False
                    for alternative_group in set(groups) - set([unique_group]):
                        lookup = {}
                        for field in alternative_group:
                            try:
                                lookup[field] = new_row[field]
                            except KeyError:
                                continue
                        if len(lookup.keys()) == len(alternative_group):
                            if _find_data(merged_data, lookup):
                                # exists - ignore it...
                                exists_in_results = True
                                break
                    if not exists_in_results and plugin != db_plugin_name:
                        # we can add it
                        merged_data.append(new_row.copy())
    return merged_data

