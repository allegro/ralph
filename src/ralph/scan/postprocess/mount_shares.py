# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.db.models import Q

from ralph.discovery.models import (
    Device,
    DiskShare,
    DiskShareMount,
    IPAddress,
)
from ralph.scan.automerger import select_data
from ralph.scan.data import (
    append_merged_proposition,
    find_devices,
    get_external_results_priorities,
    get_device_data,
    merge_data,
)


logger = logging.getLogger("MOUNT_SHARES")


def _shares_in_results(data):
    shares_in_device, shares_in_subdevice = False, False
    for plugin_name, plugin_result in data.iteritems():
        if plugin_result['status'] == 'error':
            continue
        if 'device' not in plugin_result:
            continue
        if 'disk_shares' in plugin_result['device']:
            shares_in_device = True
        for subdevice in plugin_result['device'].get('subdevices', []):
            if 'disk_shares' in subdevice:
                shares_in_subdevice = True
                break
    return shares_in_device, shares_in_subdevice


def _it_is_3par(wwn):
    return wwn[1:7] == '0002AC'


def _create_or_update_share_mount(ip, device, share_mount):
    share_address = None
    if share_mount.get('address'):
        try:
            share_address = IPAddress.objects.get(
                address=share_mount['address']
            )
        except IPAddress.DoesNotExist:
            pass
    try:
        share = DiskShare.objects.get(
            wwn=share_mount['serial_number']
        )
    except DiskShare.DoesNotExist:
        logger.warning(
            '%s%sNo share found for share mount: '
            'WWN=%s; Volume=%s; device=%s; venture=%s; device_ip=%s' % (
                '(3PAR) ' if _it_is_3par(
                    share_mount['serial_number']
                ) else '',
                '(virtual) ' if share_mount.get(
                    'is_virtual', False
                ) else '',
                share_mount['serial_number'],
                share_mount.get('volume'),
                device,
                device.venture,
                ip.address
            )
        )
        return False, None
    try:
        mount = DiskShareMount.objects.get(device=device, share=share)
    except DiskShareMount.DoesNotExist:
        mount = DiskShareMount(
            device=device,
            share=share,
        )
        logger.info(
            '%s%sCreate mount point on device %s (venture=%s). '
            'Share WWN=%s; Volume=%s; Share label=%s; IP address=%s' % (
                '(3PAR) ' if _it_is_3par(
                    share_mount['serial_number']
                ) else '',
                '(virtual) ' if share_mount.get(
                    'is_virtual', False
                ) else '',
                device,
                device.venture,
                share_mount['serial_number'],
                share_mount.get('volume'),
                share.label,
                ip.address
            )
        )
    else:
        logger.info(
            '%s%sMount point on device %s (venture=%s) exists. '
            'Share WWN=%s; Volume=%s; Share label=%s; IP address=%s' % (
                '(3PAR) ' if _it_is_3par(
                    share_mount['serial_number']
                ) else '',
                '(virtual) ' if share_mount.get(
                    'is_virtual', False
                ) else '',
                device,
                device.venture,
                share_mount['serial_number'],
                share_mount.get('volume'),
                share.label,
                ip.address
            )
        )
    if share_mount.get('size'):
        mount.size = share_mount['size']
    if share_mount.get('volume'):
        mount.volume = share_mount['volume']
    if share_address:
        mount.address = share_address
    mount.is_virtual = share_mount.get('is_virtual', False)
    mount.save()
    return True, mount


def _append_shares_to_device(ip, device, data, external_priorities={}):
    device_data = get_device_data(device)
    full_data = merge_data(
        data,
        {
            'database': {'device': device_data},
        },
        only_multiple=True,
    )
    append_merged_proposition(full_data, device, external_priorities)
    selected_data = select_data(full_data, external_priorities)
    parsed_mounts = set()
    for share_mount in selected_data.get('disk_shares', []):
        status, mount = _create_or_update_share_mount(ip, device, share_mount)
        if mount:
            parsed_mounts.add(mount.pk)
    device.disksharemount_set.exclude(pk__in=parsed_mounts).delete()


def _append_shares_to_subdevice(ip, device, shares_data):
    parsed_mounts = set()
    for share_mount in shares_data:
        status, mount = _create_or_update_share_mount(ip, device, share_mount)
        if mount:
            parsed_mounts.add(mount.pk)
    device.disksharemount_set.exclude(pk__in=parsed_mounts).delete()


def _mount_shares(ip, data):
    shares_in_device, shares_in_subdevice = _shares_in_results(data)
    if not shares_in_device and not shares_in_subdevice:
        return  # No reason to run it.
    external_priorities = get_external_results_priorities(data)
    # main devices
    if shares_in_device:
        devices = find_devices(data)
        if len(devices) == 1:
            _append_shares_to_device(ip, devices[0], data, external_priorities)
        else:
            if len(devices) == 0:
                logger.warning(
                    'No device found for the IP address %s. '
                    'There are some shares.' % ip.address
                )
            else:
                logger.warning(
                    'Many devices found for the IP address %s. '
                    'There are some shares.' % ip.address
                )
    # subdevices
    if shares_in_subdevice:
        for plugin_name, plugin_result in data.iteritems():
            if plugin_result['status'] == 'error':
                continue
            if 'device' not in plugin_result:
                continue
            for subdev_data in plugin_result['device'].get('subdevices', []):
                if 'disk_shares' not in subdev_data:
                    continue
                serials = set()
                if subdev_data.get('serial_number'):
                    serials.add(subdev_data['serial_number'])
                macs = set()
                for mac in subdev_data.get('mac_addresses', []):
                    macs.add(mac)
                devices = Device.admin_objects.filter(
                    Q(sn__in=serials) |
                    Q(ethernet__mac__in=macs)
                ).distinct()
                if len(devices) == 1:
                    _append_shares_to_subdevice(
                        ip,
                        devices[0],
                        subdev_data['disk_shares']
                    )
                else:
                    if len(devices) == 0:
                        logger.warning(
                            'No subdevice found for the hypervisor IP '
                            'address %s. SNs: %r; MACs: %r. There are some '
                            'shares.' % (
                                ip.address,
                                serials,
                                macs
                            )
                        )
                    else:
                        logger.warning(
                            'Many subdevices found for the hypervisor IP '
                            'address %s. Devices: %r. There are some '
                            'shares.' % (
                                ip.address,
                                devices
                            )
                        )


def run_job(ip, **kwargs):
    data = kwargs.get('plugins_results', {})
    _mount_shares(ip, data)
