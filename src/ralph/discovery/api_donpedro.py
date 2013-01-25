#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import traceback

from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle
from django.conf import settings
from lck.django.common.models import MACAddressField
from lck.django.common import remote_addr, nested_commit_on_success

from ralph.discovery.models import (Device, DeviceType, IPAddress, Memory,
                                    Processor, ComponentModel, ComponentType,
                                    OperatingSystem, Storage, DiskShare,
                                    DiskShareMount, FibreChannel,
                                    MAC_PREFIX_BLACKLIST, EthernetSpeed)
from ralph.util import Eth
from ralph.discovery.models_history import DiscoveryWarning


THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFREME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']
SAVE_PRIORITY = 51


logger = logging.getLogger(__name__)


class NoRequiredDataError(Exception):
    pass


class NoRequiredIPAddressError(NoRequiredDataError):
    pass


def save_processors(processors, dev):
    indexes = []
    for p in processors:
        cpuname = p.get('label')
        try:
            index = int(p.get('index')[3:]) + 1  # CPU0
            speed = int(p.get('speed'))
            cores = int(p.get('cores'))
        except ValueError:
            continue
        indexes.append(index)
        cpu, created = Processor.concurrent_get_or_create(
            device=dev,
            index=index,
            defaults={
                'label': cpuname,
                'speed': speed,
                'cores': cores,
            },
        )
        is64bit = p.get('is64bit') == 'true'
        name = 'CPU %s%s %s%s' % (
            '64bit ' if is64bit else '',
            cpuname, '%dMhz' % speed if speed else '',
            ' multicore' if cores > 1 else '')
        cpu.model, c = ComponentModel.create(
            ComponentType.processor,
            cores=cores,
            family=cpuname,
            speed=speed,
            name=name,
            priority=SAVE_PRIORITY,
        )
        cpu.save(priority=SAVE_PRIORITY)
    for cpu in dev.processor_set.exclude(index__in=indexes):
        cpu.delete()


def save_shares(shares, dev, ip):
    wwns = []
    for s in shares:
        wwn_end = s.get('sn')
        if not wwn_end:
            continue
        try:
            share = DiskShare.objects.get(wwn__endswith=wwn_end.upper())
        except DiskShare.DoesNotExist:
            continue
        wwns.append(share.wwn)
        mount, _ = DiskShareMount.concurrent_get_or_create(device=dev,
                                                           share=share)
        mount.volume = s.get('volume')
        mount.save(update_last_seen=True)
    for mount in DiskShareMount.objects.filter(device=dev).exclude(
            share__wwn__in=wwns):
        mount.delete()


@nested_commit_on_success
def save_storage(storage, dev):
    mount_points = []
    for item in storage:
        sn = item.get('sn')
        mount_point = item.get('mountpoint')
        if not sn or not mount_point:
            continue
        label = item.get('label')
        try:
            size = int(item.get('size'))
        except ValueError:
            continue
        model_name = '{} {}MiB'.format(label, size)
        model, c = ComponentModel.create(
            ComponentType.disk,
            size=size,
            family=model_name,
            priority=SAVE_PRIORITY,
        )
        stor = None
        try:
            stor = Storage.objects.get(device=dev, mount_point=mount_point)
            if stor.sn != sn:
                try:
                    stor_found_by_sn = Storage.objects.get(sn=sn)
                    if all((
                        stor_found_by_sn.model == model,
                        stor_found_by_sn.size == size,
                        stor_found_by_sn.label == label
                    )):
                        stor.mount_point = None
                        stor.save(priotity=SAVE_PRIORITY)
                        stor = stor_found_by_sn
                        stor.device = dev
                        stor.mount_point = mount_point
                    else:
                        stor = None
                except Storage.DoesNotExist:
                    stor.sn = sn
        except Storage.DoesNotExist:
            try:
                stor = Storage.objects.get(sn=sn)
                if all((
                    stor.model == model,
                    stor.size == size,
                    stor.label == label
                )):
                    stor.device = dev
                    stor.mount_point = mount_point
                else:
                    stor = None
            except Storage.DoesNotExist:
                stor = Storage(
                    device=dev, mount_point=mount_point, sn=sn
                )
        if stor:
            stor.model = model
            stor.label = label
            stor.size = size
            stor.save(priority=SAVE_PRIORITY)
        mount_points.append(mount_point)
    dev.storage_set.exclude(
        mount_point__in=mount_points
    ).update(mount_point=None)


def save_memory(memory, dev):
    indexes = []
    index = 0
    for row in memory:
        index += 1
        indexes.append(index)
        try:
            size = int(row.get('size'))
            speed = int(row.get('speed')) if row.get('speed') else 0
        except ValueError:
            pass
        label = row.get('label')
        mem, created = Memory.concurrent_get_or_create(device=dev, index=index)
        mem.size = size
        mem.label = 'RAM %dMiB' % size
        mem.speed = speed
        family = 'Virtual Windows' if 'Virtual' in label else 'Windows'
        mem.model, c = ComponentModel.create(
            ComponentType.memory,
            family=family,
            size=size,
            speed=speed,
            priority=SAVE_PRIORITY,
        )
        mem.save(priority=SAVE_PRIORITY)
    dev.memory_set.exclude(index__in=indexes).delete()


def save_fibre_channel(fcs, dev):
    detected_fc_cards = []
    for f in fcs:
        pid = f.get('physicalid')
        model = f.get('model')
        manufacturer = f.get('manufacturer')
        fib, created = FibreChannel.concurrent_get_or_create(device=dev,
                                                             physical_id=pid)
        fib.label = f.get('label')
        fib.model, c = ComponentModel.create(
            ComponentType.fibre,
            family=manufacturer or fib.label,
            name=model or fib.label,
            priority=SAVE_PRIORITY,
        )
        fib.save(priority=SAVE_PRIORITY)
        detected_fc_cards.append(fib.pk)
    dev.fibrechannel_set.exclude(pk__in=detected_fc_cards).delete()


def str_to_ethspeed(str_value):
    if not str_value:
        return EthernetSpeed.unknown.id
    int_value = int(str_value)
    if int_value == 1000000000:
        speed = EthernetSpeed.s1gbit.id
    elif int_value == 100000000:
        speed = EthernetSpeed.s100mbit.id
    else:
        speed = EthernetSpeed.unknown.id
    return speed


def save_device_data(data, remote_ip):
    device = data['device']
    ethernets = [
        Eth(e.get('label'), MACAddressField.normalize(e.get('mac')),
            str_to_ethspeed(e.get('speed')))
        for e in data['ethernets']
        if MACAddressField.normalize(e.get('mac')) not in MAC_PREFIX_BLACKLIST]
    sn = device.get('sn')
    if not ethernets and not sn:
        raise NoRequiredDataError('No MAC addresses and no device SN.')
    ip_addresses = [
        e['ipaddress'] for e in data['ethernets'] if e['ipaddress']
    ]
    if not ip_addresses:
        raise NoRequiredIPAddressError(
            "Couldn't find any IP address for this device."
        )
    try:
        dev = Device.create(
            sn=sn,
            ethernets=ethernets,
            model_name='%s %s %s' % (
                device.get('caption'), device.get('vendor'),
                device.get('version')),
            model_type=DeviceType.unknown, priority=SAVE_PRIORITY
        )
    except ValueError as e:
        DiscoveryWarning(
            message="Failed to create device: " + str(e),
            plugin=__name__,
            ip=str(remote_ip),
        ).save()
        return None
    dev.save(priority=SAVE_PRIORITY)
    os = data['operating_system']
    o = OperatingSystem.create(dev, os_name=os.get('label'),
                               family='Windows', priority=SAVE_PRIORITY)
    o.memory = int(os['memory'])
    o.storage = int(os['storage'])
    o.cores_count = int(os['corescount'])
    o.save(priority=SAVE_PRIORITY)
    for ip in ip_addresses:
        ip_address, _ = IPAddress.concurrent_get_or_create(address=str(ip))
        ip_address.device = dev
        ip_address.is_management = False
        ip_address.save()
    save_processors(data['processors'], dev)
    save_memory(data['memory'], dev)
    save_storage(data['storage'], dev)
    save_shares(data['shares'], dev, ip_address)
    save_fibre_channel(data['fcs'], dev)
    return dev


class WindowsDeviceResource(MResource):
    def obj_create(self, bundle, request=None, **kwargs):
        ip = remote_addr(request)
        logger.debug('Got json data: %s' % bundle.data.get('data'))
        try:
            return save_device_data(bundle.data.get('data'), ip)
        except Exception:
            logger.error(traceback.format_exc())
            raise

    class Meta:
        queryset = Device.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {}
        excludes = ('save_priorities', 'max_save_priority', 'dns_info',
                    'snmp_name')
        cache = SimpleCache()
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                 expiration=EXPIRATION)

