#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ReST API for Ralph's discovery models
   -------------------------------------

Done with TastyPie.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import logging

from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle

from ralph.discovery.models import Device, DeviceModel, DeviceModelGroup,\
    DeviceType, IPAddress, Memory, Processor, ComponentModel, \
    ComponentType, OperatingSystem, Storage, DiskShare, DiskShareMount, \
    FibreChannel, MAC_PREFIX_BLACKLIST
from ralph.util import Eth

from lck.django.common.models import MACAddressField
from lck.django.common import remote_addr
from django.conf import settings

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
        index = int(p['index'][3:])+1 #CPU0
        indexes.append(index)
        speed = int(p.get('speed'))
        cores = int(p.get('cores'))
        cpuname = p.get('label')
        cpu, created = Processor.concurrent_get_or_create(
                device=dev, index=index)
        cpu.label = cpuname
        cpu.speed = speed
        cpu.cores = cores
        extra = '%s %s %s ' % (p.get('label'), speed, cores)
        is64bit = p.get('is64bit') or False
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
        try:
            share = DiskShare.objects.get(wwn__endswith=wwn_end)
        except DiskShare.DoesNotExist:
            continue
        wwns.append(share.wwn)
        ipaddr = dev.ipaddress_set.all()[0]
        mount, _ = DiskShareMount.concurrent_get_or_create(
            device=ipaddr.device, label=s.get('label'))
        mount.volume = s['volume']
        mount.save(update_last_seen=True)
    for mount in DiskShareMount.objects.filter(device=dev).exclude( share__wwn__in=wwns):
        mount.delete()


def save_storage(storage, dev):
    for s in storage:
        if not s['sn']:
            continue
        stor, created = Storage.concurrent_get_or_create(device=dev, sn=s['sn'])
        stor.size = int(s['size'])
        stor.label = s['label']
        stor.mount_point = s.get('mountpoint')
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, type=ComponentType.disk.id,
            family='', name=stor.label,
        )
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)
    for storage_to_delete in dev.storage_set.exclude(sn__in=[s['sn'] for s in storage]):
        storage_to_delete.delete()


def save_memory(memory, dev):
    indexes = []
    memory_total_size = 0
    index = 0
    for row in memory:
        index+=1
        size = int(row['size']); speed = int(row['speed']) if row['speed'] else 0
        memory_total_size += size
        label = row['index'] #eg: 'DIMM-2A'
        indexes.append(index)
        mem, created = Memory.concurrent_get_or_create(device=dev,
                label=label,
                index=index)
        mem.label = label
        mem.size = size
        mem.model, c = ComponentModel.concurrent_get_or_create(
            family='Windows RAM', size=size, speed=speed,
            type=ComponentType.memory.id, extra_hash='')
        mem.model.name = 'RAM Windows %dMiB' % size
        mem.model.size = size
        mem.model.save()
        mem.save(priority=SAVE_PRIORITY)
    dev.memory_set.exclude(index__in=indexes).delete()


def save_fibre_channel(fcs, dev):
    detected_fc_cards = []
    for f in fcs:
        pid = f.get('physicalid')
        fib, created = FibreChannel.concurrent_get_or_create(device=dev,
            physical_id=pid)
        fib.label = f.get('label')
        extra = fib.label
        fib.model, c = ComponentModel.concurrent_get_or_create(
            type=ComponentType.fibre.id, family=f.get('manufacturer'),
            extra_hash=hashlib.md5(extra).hexdigest())
        fib.model.extra = extra
        fib.model.name = f.get('model')
        fib.model.save(priority=SAVE_PRIORITY)
        fib.save(priority=SAVE_PRIORITY)
        detected_fc_cards.append(fib.pk)
    dev.fibrechannel_set.exclude(pk__in=detected_fc_cards).delete()


def save_device_data(data, remote_ip):
    device = data['device']
    shares = data['shares']
    fcs = data['fcs']
    storage = data['storage']
    memory = data['memory']
    processors = data['processors']
    os = data['operating_system']
    device = data['device']
    ethernets = [Eth(e.get('label'), e['mac'].replace(':', ''), e.get('speed')) for
        e in data['ethernets'] if MACAddressField.normalize(e.get('mac'))[0:6]
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
           family='Windows')
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


class WindowsDeviceResource(MResource):
    def obj_create(self, bundle, request=None, **kwargs):
        ip = remote_addr(request)
        logger.debug('Got json data: %s' % bundle.data.get('data'))
        try:
            return save_device_data(bundle.data.get('data'), ip)
        except Exception as e:
            logger.error(e)
            raise

    def obj_update(self, bundle, request=None, **kwargs):
        pass

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

