#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import logging
import traceback

from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle
from django.conf import settings
from lck.django.common.models import MACAddressField
from lck.django.common import remote_addr

from ralph.discovery.models import (Device, DeviceType, IPAddress, Memory,
    Processor, ComponentModel, ComponentType, OperatingSystem, Storage,
    DiskShare, DiskShareMount, FibreChannel, MAC_PREFIX_BLACKLIST, EthernetSpeed )
from ralph.util import Eth


THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFREME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']
SAVE_PRIORITY = 51


logger = logging.getLogger(__name__)

class NoMACError(Exception):
    pass


def save_processors(processors, dev):
    indexes = []
    for p in processors:
        cpuname = p.get('label')
        try:
            index = int(p.get('index')[3:]) + 1 #CPU0
            speed = int(p.get('speed'))
            cores = int(p.get('cores'))
        except ValueError:
            continue
        indexes.append(index)
        cpu, created = Processor.concurrent_get_or_create(
            device=dev, index=index)
        cpu.label = cpuname
        cpu.speed = speed
        cpu.cores = cores
        is64bit = p.get('is64bit') == 'true'
        extra = '%s %s %s ' % (p.get('manufacturer'),
            p.get('version'), '64bit' if is64bit else '')
        name = 'CPU %s%s %s %s' % (
            '64bit ' if is64bit else '',
            cpuname, '%dMhz' % speed if speed else '',
            'multicore' if cores else '')
        cpu.model, c = ComponentModel.concurrent_get_or_create(
            speed=speed, type=ComponentType.processor.id,
            family=cpuname,
            cores=cores, extra_hash=hashlib.md5(extra).hexdigest())
        cpu.model.extra = extra
        cpu.model.name = name
        cpu.model.save(priority=SAVE_PRIORITY)
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


def save_storage(storage, dev):
    mount_points = []
    for s in storage:
        if not s.get('sn'):
            continue
        stor, created = Storage.concurrent_get_or_create(device=dev,
            sn=s.get('sn'))
        try:
            stor.size = int(s.get('size'))
        except ValueError:
            pass
        stor.label = s.get('label')
        model = '{} {}MiB'.format(stor.label, stor.size)
        stor.mount_point = s.get('mountpoint')
        mount_points.append(stor.mount_point)
        extra = ''
        stor.model, c = ComponentModel.concurrent_get_or_create(size=stor.size,
            type=ComponentType.disk.id, speed=0, cores=0, extra=extra,
            extra_hash=hashlib.md5(extra).hexdigest(), family=model)
        stor.model.name = model
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)
    dev.storage_set.exclude(mount_point__in=mount_points).delete()


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
        family = 'Virtual' if 'Virtual' in label else ''
        extra = '%s %dMiB %s %s' % (label, size, speed, row.get('caption'))
        mem.model, c = ComponentModel.concurrent_get_or_create(
            family=family, size=size, speed=speed, type=ComponentType.memory.id,
            extra_hash=hashlib.md5(extra).hexdigest())
        mem.model.extra = extra
        mem.model.name = 'RAM Windows %dMiB' % size
        mem.model.save()
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
        extra = '%s %s %s %s' % (fib.label, pid, manufacturer, model)
        fib.model, c = ComponentModel.concurrent_get_or_create(
            type=ComponentType.fibre.id, family=fib.label,
            extra_hash=hashlib.md5(extra).hexdigest())
        fib.model.extra = extra
        fib.model.name = model if model else fib.label
        fib.model.save(priority=SAVE_PRIORITY)
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
    shares = data['shares']
    fcs = data['fcs']
    storage = data['storage']
    memory = data['memory']
    processors = data['processors']
    os = data['operating_system']
    device = data['device']
    ethernets = [Eth(e.get('label'), MACAddressField.normalize(e.get('mac')),
        str_to_ethspeed(e.get('speed'))) for
        e in data['ethernets'] if MACAddressField.normalize(e.get('mac'))
        not in MAC_PREFIX_BLACKLIST]
    if not ethernets:
        raise NoMACError('No MAC addresses.')
    dev = Device.create(
        sn=device.get('sn'),
        ethernets=ethernets,
        model_name='%s %s %s' % (device.get('caption'),
        device.get('vendor'), device.get('version')),
        model_type=DeviceType.unknown, priority=SAVE_PRIORITY
    )
    dev.save(priority=SAVE_PRIORITY)
    if not dev.operatingsystem_set.exists():
        o = OperatingSystem.create(dev,
            os_name=os.get('label'),
            family='Windows',
        )
        o.memory = int(os['memory'])
        o.storage = int(os['storage'])
        o.cores_count = int(os['corescount'])
        o.save()
    ip_address, _ = IPAddress.concurrent_get_or_create(address=str(remote_ip))
    ip_address.device = dev
    ip_address.is_management = False
    ip_address.save()
    save_processors(processors, dev)
    save_memory(memory, dev)
    save_storage(storage, dev)
    save_shares(shares, dev, ip_address)
    save_fibre_channel(fcs, dev)
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
