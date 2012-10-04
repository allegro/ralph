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
SAVE_PRIORITY = 10


class NoMACError(Exception):
    pass

def save_device_data(data, remote_ip):
    device = data['device']
    shares = data['shares']
    fcs = data['fcs']
    storage = data['storage']
    operating_system = data['operating_system']
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
        OperatingSystem.create(dev,
            os_name=operating_system.get('label'),
           family='Windows').save()
    ip_address, _ = IPAddress.concurrent_get_or_create(address=str(remote_ip))
    ip_address.device = dev
    ip_address.is_management = False
    ip_address.save()
    processors = data['processors']
    for cpu in dev.processor_set.exclude(index__in=[int(p['index'][3:]) for p in processors]):
        cpu.delete()
    for p in processors:
        index = p['index'][3:] #CPU0
        label = p['index']
        speed = int(p.get('speed'))
        cores = int(p.get('cores'))
        cpu, created = Processor.concurrent_get_or_create(
                device=dev, index=index)
        cpu.label = label
        cpu.speed = speed
        cpu.cores = cores
        cpu.model, c = ComponentModel.concurrent_get_or_create(
            speed=speed, type=ComponentType.processor.id,
            cores=cores)
        cpu.model.save(priority=SAVE_PRIORITY)
        cpu.save(priority=SAVE_PRIORITY)
    for storage_to_delete in dev.storage_set.exclude(sn__in=[s['sn'] for s in storage]):
        storage_to_delete.delete()
    for s in storage:
        if not s['sn']:
            continue
        stor, created = Storage.concurrent_get_or_create(device=dev, sn=s['sn'])
        stor.size = int(s['size'])
        stor.label = s['label']
        stor.mount_point = s.get('mountpoint')
        stor.model, c = ComponentModel.concurrent_get_or_create(
            size=stor.size, type=ComponentType.disk.id,
            family='', name=label,
        )
        stor.model.name =  '{} {}MiB'.format(stor.label, stor.size)
        stor.model.save(priority=SAVE_PRIORITY)
        stor.save(priority=SAVE_PRIORITY)
    wwns = []
    for share in shares:
        wwn_end = share.get('wwn')
        try:
            share = DiskShare.objects.get(wwn__endswith=wwn_end)
        except DiskShare.DoesNotExist:
            continue
        wwns.append(share.wwn)
    for share in shares:
            ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=share['ip'])
            mount, created = DiskShareMount.concurrent_get_or_create(
                    address=ipaddr, device=ipaddr.device, server=dev)
            mount.volume = share['volume']
            mount.save(update_last_seen=True)
    for mount in DiskShareMount.objects.filter(
                server=dev
            ).exclude(
                share__wwn__in=wwns
        ):
        mount.delete()
    return dev

class WindowsDeviceResource(MResource):
    def obj_create(self, bundle, request=None, **kwargs):
        ip = remote_addr(request)
        return import_device_data(bundle.data.get('data'), ip)

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

