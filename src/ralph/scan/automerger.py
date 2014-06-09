# -*- coding: utf-8 -*-

"""
Save merged scan results data.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django_rq
import logging
import rq
import time

from django.conf import settings
from django.db import models as db

from ralph.discovery.models_device import Device
from ralph.discovery.models_network import IPAddress
from ralph.scan.data import (
    append_merged_proposition,
    device_from_data,
    get_device_data,
    get_external_results_priorities,
    merge_data,
    set_device_data,
)
from ralph.scan.errors import AutomergerError
from ralph.scan.util import update_scan_summary


SAVE_PRIORITY = 205


logger = logging.getLogger("SCAN")


def _get_queue_name():
    if 'scan_automerger' in settings.RQ_QUEUES:
        return 'scan_automerger'
    return 'default'


def _enqueue_save_job_results(job_id):
    queue = django_rq.get_queue(_get_queue_name())
    queue.enqueue_call(
        func=_save_job_results,
        kwargs={
            'job_id': job_id,
            'start_ts': int(time.time()),
        },
        timeout=300,
        result_ttl=0,
    )


def _get_best_plugin_for_component(
    component,
    plugins,
    external_priorities={},
    is_management=False
):
    if 'merged' in plugins:
        return 'merged'
    top_plugin = ''
    top_priority = 0
    # check local plugins
    for plugin in plugins:
        if plugin not in settings.SCAN_PLUGINS:
            continue
        if 'results_priority' not in settings.SCAN_PLUGINS[plugin]:
            continue
        priority = settings.SCAN_PLUGINS[plugin]['results_priority'].get(
            component, 0,
        )
        if priority > top_priority:
            top_priority = priority
            top_plugin = plugin
    # check external plugins
    for plugin in plugins:
        if plugin not in external_priorities:
            continue
        priority = external_priorities[plugin].get(component, 0)
        if priority > top_priority:
            top_priority = priority
            top_plugin = plugin
    if not top_plugin or (component == 'hostname' and is_management):
        # hostname for management ip address must be ignored - it could
        # overwrite real device hostname
        top_plugin = 'database'
    return top_plugin


def _find_data_by_plugin(data, plugin):
    for sources, results in data.iteritems():
        if plugin in sources:
            return results


def select_data(data, external_priorities={}, is_management=False):
    selected_data = {}
    for component, result in data.iteritems():
        available_plugins = set()
        for plugins, plugins_result in result.iteritems():
            available_plugins |= set(plugins)
        best_plugin = _get_best_plugin_for_component(
            component,
            available_plugins,
            external_priorities,
            is_management
        )
        best_data_for_component = _find_data_by_plugin(result, best_plugin)
        if best_data_for_component is None:
            continue
        selected_data[component] = best_data_for_component
    return selected_data


def _find_devices(result):
    ids = set(
        r['device']['id']
        for r in result.itervalues() if 'id' in r.get('device', {})
    )
    serials = set(
        r['device']['serial_number']
        for r in result.itervalues() if 'serial_number' in r.get('device', {})
    )
    macs = set()
    for r in result.itervalues():
        macs |= set(r.get('device', {}).get('mac_addresses', []))
    return Device.admin_objects.filter(
        db.Q(id__in=ids) |
        db.Q(sn__in=serials) |
        db.Q(ethernet__mac__in=macs)
    ).distinct(), ids, serials, macs


def _save_job_results(job_id, start_ts):
    if (int(time.time()) - start_ts) > 86100:  # 24h - 5min
        return
    try:
        job = rq.job.Job.fetch(job_id, django_rq.get_connection())
    except rq.exceptions.NoSuchJobError:
        return  # job with this id does not exist...
    if job.result is None and not job.is_failed:
        # we must wait...
        _enqueue_save_job_results(job_id)
        return
    elif job.is_failed:
        # nothing to do...
        return
    external_priorities = get_external_results_priorities(job.result)
    # management?
    is_management = False
    if job.args:
        try:
            is_management = IPAddress.objects.filter(
                address=job.args[0]
            ).values_list(
                'is_management', flat=True
            )[0]
        except IndexError:
            pass
    # first... update device
    devices, ids_lookup, sn_lookup, macs_lookup = _find_devices(job.result)
    if len(devices) > 1:
        raise AutomergerError(
            'Many devices found for: ids=%s, sn=%s, macs=%s' % (
                ids_lookup, sn_lookup, macs_lookup
            )
        )
    used_serial_numbers = set()
    used_mac_addresses = set()
    for device in devices:
        device_data = get_device_data(device)
        if 'serial_number' in device_data:
            used_serial_numbers |= set([device_data['serial_number']])
        if 'mac_addresses' in device_data:
            used_mac_addresses |= set(device_data['mac_addresses'])
        data = merge_data(
            job.result,
            {
                'database': {'device': device_data},
            },
            only_multiple=True,
        )
        append_merged_proposition(data, device, external_priorities)
        selected_data = select_data(data, external_priorities, is_management)
        set_device_data(device, selected_data, save_priority=SAVE_PRIORITY)
        device.save(priority=SAVE_PRIORITY)
    # now... we create new devices from `garbage`
    if not devices:
        garbage = {}
        for plugin_name, plugin_result in job.result.items():
            if 'device' not in plugin_result:
                continue
            if 'serial_number' in plugin_result['device']:
                if plugin_result['device'][
                    'serial_number'
                ] in used_serial_numbers:
                    continue
            if 'mac_addresses' in plugin_result['device']:
                if set(
                    plugin_result['device']['mac_addresses'],
                ) != set(
                    plugin_result['device']['mac_addresses'],
                ) - used_mac_addresses:
                    continue
            if any((
                plugin_result['device'].get('serial_number'),
                plugin_result['device'].get('mac_addresses'),
            )):
                garbage[plugin_name] = plugin_result
        if garbage:
            data = merge_data(garbage)
            selected_data = select_data(data, external_priorities)
            if all((
                any(
                    (
                        selected_data.get('serial_number'),
                        selected_data.get('mac_addresses', []),
                    )
                ),
                any(
                    (
                        selected_data.get('model_name'),
                        selected_data.get('type'),
                    )
                ),
            )):
                device_from_data(selected_data, save_priority=SAVE_PRIORITY)
    # mark this scan results
    update_scan_summary(job)


def save_job_results(job_id):
    _enqueue_save_job_results(job_id)
