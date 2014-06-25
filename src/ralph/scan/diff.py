# -*- coding: utf-8 -*-

"""
Set of functions to make diff from Scan results.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.encoding import force_unicode

from ralph.discovery.models import DeviceType
from ralph.scan.data import UNIQUE_FIELDS_FOR_MERGER


RAW_DEVICE_TYPES = [
    choice_name
    for _, choice_name in DeviceType()
]


def _sort_dict_by_multiple_fields_values(keynames):
    def getit(adict):
        composite = []
        for key in keynames:
            if key in adict:
                composite.append(adict[key])
        return composite
    return getit


def sort_results(data, ignored_fields=set(['device'])):
    """
    Sort results for all components and all plugins.
    """

    for component, results in data.iteritems():
        if component not in UNIQUE_FIELDS_FOR_MERGER:
            continue
        for sources, plugins_data in results.iteritems():
            keynames = set()
            for fields_group in UNIQUE_FIELDS_FOR_MERGER[component]:
                for field in fields_group:
                    if field in ignored_fields:
                        continue
                    keynames.add(field)
            if keynames:
                plugin_data = sorted(
                    plugins_data,
                    key=_sort_dict_by_multiple_fields_values(keynames),
                )
            data[component][sources] = plugin_data


def _get_matched_row(rows, lookup):
    """
    Return row that matches lookup fields.
    """

    for index, row in enumerate(rows):
        matched = True
        for field, value in lookup.items():
            if force_unicode(row.get(field, '')).strip() != value:
                matched = False
                break
        if matched:
            return index, row
    return None, None


def _compare_dicts(
    ldict,
    rdict,
    ignored_fields=set(['device', 'index', 'model_name'])
):
    """
    Compare two dicts and return comparison status (match), diff and set of
    keys that are available in compared dicts.
    """

    match = True
    diff = {}
    keys = (set(ldict.keys()) | set(rdict.keys())) - ignored_fields
    for key in keys:
        lvalue = force_unicode(ldict.get(key, '')).strip()
        rvalue = force_unicode(rdict.get(key, '')).strip()
        if lvalue and not rvalue:
            match = False
            diff[key] = {
                'status': b'-',
                'left_value': lvalue,
                'right_value': '',
            }
        elif not lvalue and rvalue:
            match = False
            diff[key] = {
                'status': b'+',
                'left_value': '',
                'right_value': rvalue,
            }
        else:
            if lvalue == rvalue:
                diff[key] = {
                    'status': b'',
                    'left_value': lvalue,
                    'right_value': rvalue,
                }
            else:
                match = False
                diff[key] = {
                    'status': b'?',
                    'left_value': lvalue,
                    'right_value': rvalue,
                }
    return match, diff, keys


def _compare_lists(*args):
    """
    Compare two or more lists. Return True if all equals.
    """

    if not args:
        return True
    compared_item = set(args[0])
    for item in args[1:]:
        if compared_item != set(item):
            return False
    return True


def _compare_strings(*args):
    """
    Compare two or more strings. Return True if all equals.
    """

    if not args:
        return True
    compared_item = force_unicode(args[0]).strip()
    for item in args[1:]:
        if compared_item != force_unicode(item).strip():
            return False
    return True


def _find_database_key(results):
    """
    The same data from different plugins are connected together in results
    under the same key. This key is just a tuple (e.q. (database, puppet)).
    This function returns tuple which contains "database" element.
    """

    for sources in results.iterkeys():
        if 'database' in sources:
            return sources


def _sanitize_component_values(values=[]):
    result = []
    for value in values:
        for device_type in RAW_DEVICE_TYPES:
            if '(%s)' % device_type in value:
                value = value.replace('(%s)' % device_type, '').strip()
        result.append(value)
    return result


def diff_results(data, ignored_fields=set(['device', 'model_name'])):
    """
    Make diff from Scan results.
    """

    diffs = {}
    for component, results in data.iteritems():
        if component == 'subdevices':
            continue  # skipped because this is not component...
        db_results_key = _find_database_key(results)
        if not db_results_key:
            continue  # incomplete data
        diff_result = {
            'is_equal': False,
            'meta': {'no_value': []},
        }
        if component not in UNIQUE_FIELDS_FOR_MERGER:
            if isinstance(results[db_results_key], list):
                diff_result.update({
                    'is_equal': _compare_lists(*tuple(results.values())),
                    'type': 'lists',
                })
            else:
                component_values = results.values()
                if component == 'model_name':
                    component_values = _sanitize_component_values(
                        component_values
                    )
                elif (component == 'type' and
                      set(component_values) == set(['unknown'])):
                    diff_result['meta']['no_value'].append(component)
                diff_result.update({
                    'is_equal': _compare_strings(*tuple(component_values)),
                    'type': 'strings',
                })
        else:
            diff_result.update({
                'type': 'dicts',
                'diff': [],
            })
            database = results.get(db_results_key, [])
            merged = results.get(('merged',), [])
            database_parsed_rows = set()
            merged_parsed_rows = set()
            headers = set()
            add_items_count = 0
            remove_items_count = 0
            change_items_count = 0
            for index, items in enumerate(database):
                for field_group in UNIQUE_FIELDS_FOR_MERGER[component]:
                    # some rows could be return with the same index by
                    # different lookups
                    if index in database_parsed_rows:
                        break
                    lookup = {}
                    for field in field_group:
                        if field in ignored_fields:
                            continue
                        field_db_value = force_unicode(
                            items.get(field, '')
                        ).strip()
                        if not field_db_value:
                            continue
                        lookup[field] = field_db_value
                    if lookup:
                        matched_index, matched_row = _get_matched_row(
                            merged,
                            lookup,
                        )
                        if matched_row:
                            database_parsed_rows.add(index)
                            merged_parsed_rows.add(matched_index)
                            status, row_diff, rows_keys = _compare_dicts(
                                items,
                                matched_row,
                            )
                            diff_result['diff'].append({
                                'status': b'?' if not status else b'',
                                'items': items,
                                'dict_diff': row_diff,
                            })
                            if not status:
                                change_items_count += 1
                            headers |= rows_keys
                if index not in database_parsed_rows:
                    diff_result['diff'].append({
                        'status': b'-',
                        'items': items,
                        'dict_diff': None,
                    })
                    remove_items_count += 1
                    headers |= set(items.keys())
            for index, items in enumerate(merged):
                if index not in merged_parsed_rows:
                    diff_result['diff'].append({
                        'status': b'+',
                        'items': items,
                        'dict_diff': None,
                    })
                    add_items_count += 1
                    headers |= set(items.keys())
            headers -= ignored_fields
            headers -= {'index'}
            diff_result.update({
                'is_equal': all((
                    add_items_count == 0,
                    remove_items_count == 0,
                    change_items_count == 0,
                )),
                'meta': {
                    'add_items_count': add_items_count,
                    'remove_items_count': remove_items_count,
                    'change_items_count': change_items_count,
                    'headers': headers,
                },
            })
        diffs[component] = diff_result
    return diffs
