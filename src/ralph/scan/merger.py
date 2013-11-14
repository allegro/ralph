# -*- coding: utf-8 -*-

"""
Scan results merger.

It's merge results from all available plugins with data stored in database.
The main idea of this merger is to use all possible unique keys for merged
component. It's similar to DB `unique` and `unique together` keys.
E.g.:
1. For disks will be:
    - serial_number
    - device, mount_point
2. For fibrechannel cards will be:
    - device, physical_id

The same idea is used when we try make diff.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.conf import settings


logger = logging.getLogger("SCAN")


def _get_results_quality(plugin, component):
    try:
        return settings.SCAN_PLUGINS[plugin]['results_quality'][component]
    except KeyError:
        logger.warning(
            "Result quality for plugin '%s' and component '%s' not found." % (
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
                    'quality': _get_results_quality(plugin, component),
                } for plugin in plugins
            ],
            key=lambda k: k['quality'],
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
    plugins = usefull_data.keys()
    try:
        plugins.remove(db_plugin_name)
    except ValueError:
        pass
    ranked_plugins = _get_ranked_plugins_list(plugins, component)
    if db_plugin_name in data:
        ranked_plugins.append(db_plugin_name)
    merged_data = []
    for plugin in ranked_plugins:
        groups = usefull_data.get(plugin, {}).keys()
        for unique_group in groups:
            for new_row in usefull_data[plugin][unique_group]:
                lookup = {}
                for field in unique_group:
                    lookup[field] = new_row[field]
                current_row = _find_data(merged_data, lookup)
                if current_row:
                    if plugin == db_plugin_name:
                        for field, value in new_row.iteritems():
                            if not current_row.get(field):
                                current_row[field] = value
                    else:
                        current_row.update(new_row)
                else:
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
                                exists_in_results = True
                                break
                    if not exists_in_results and plugin != db_plugin_name:
                        merged_data.append(new_row.copy())
    return merged_data

