# -*- coding: utf-8 -*-

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
    usefull_data = {}
    useless_data = {}
    for plugin, plugin_results in data.iteritems():
        for row in plugin_results:
            is_useless = True
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
                    is_useless = False
            if is_useless:
                if plugin not in useless_data:
                    useless_data[plugin] = []
                useless_data[plugin].append(row)
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

