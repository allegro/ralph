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
    return sorted(
        [
            {
                'plugin': plugin,
                'quality': _get_results_quality(plugin, component),
            } for plugin in plugins
        ],
        key=lambda k: k['quality'],
    )


def _find_data(rows, lookup):
    for row in rows:
        matched = True
        for field in lookup.keys():
            if (
                field not in row or
                not row[field] or
                str(lookup[field]).lower() != str(row[field]).lower()
            ):
                matched = False
                break
        if matched:
            return row


def merge(component, data, unique_fields):
    usefull_data = {}
    useless_data = {}
    for plugin, plugin_results in data.iteritems():
        if plugin == 'db':
            continue
        for row in plugin_results:
            is_useless = True
            for unique_group in unique_fields:
                fields = set([
                    field for field in unique_group
                    if field in row and row[field]
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
    ranked_plugins = _get_ranked_plugins_list(usefull_data.keys(), component)
    merged_data = data.get('db', [])
    for plugin in ranked_plugins:
        groups = usefull_data.get(plugin, {}).keys()
        for unique_group in groups:
            for new_row in usefull_data[plugin][unique_group]:
                lookup = {}
                for field in unique_group:
                    lookup[field] = new_row[field]
                current_row = _find_data(merged_data, lookup)
                if current_row:
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
                    if not exists_in_results:
                        merged_data.append(new_row)
    return merged_data

