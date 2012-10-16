#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import date, timedelta, datetime, time
import math

from django.db import models as db
from django.utils.html import escape
from django.conf import settings

from ralph.discovery.models import (DeviceType, ComponentModelGroup, Processor,
                                    DiskShare, EthernetSpeed, OperatingSystem)


def get_device_price(device):
    """
    The quoted price, including all subtractions and additions from other
    devices.
    """
    price = get_device_raw_price(device)
    price += get_device_external_price(device)
    return max(0, price)


def get_device_external_price(device):
    """The price of all external subtractions additions for a device."""

    price = 0
    # Subtract the price of virtual servers, so they don't count 2x
    price -= get_device_virtuals_price(device)
    # Subtract the price of exported disk shares
    price -= get_device_exported_storage_price(device)
    if device.model and device.model.type == DeviceType.blade_system.id:
        # Subtract the prices taken by blades
        for d in device.child_set.filter(
                model__type=DeviceType.blade_server.id):
            price -= get_device_chassis_price(d)
    elif device.model and device.model.type == DeviceType.blade_server.id:
        # Add the price taken from the blade system
        price += get_device_chassis_price(device)
    # Add the prices of the remote disk shares
    remote_storage_price = math.fsum(m.get_price()
                                     for m in device.disksharemount_set.all())
    price += remote_storage_price
    return price



def get_device_raw_price(device):
    """Purchase price of this device, before anything interacts with it."""
    today_midnight = datetime.combine(datetime.today(), time())
    if device.deprecation_date and today_midnight >= device.deprecation_date:
        return 0
    return device.price or get_device_auto_price(device)


def get_device_cost(device):
    """Return the monthly cost of this device."""

    price = get_device_price(device)
    deprecation_kind = device.get_deprecation_kind()
    if deprecation_kind is not None:
        cost = price / deprecation_kind.months
    else:
        cost = 0
    margin = device.get_margin() or 0
    cost = cost * (1 + margin / 100) + get_device_additional_costs(device)
    return cost


def get_device_additional_costs(device):
    """Return additional monthly costs for this device, e.g. Splunk usage."""

    cost = 0
    last_month = date.today() - timedelta(days=31)
    splunk = device.splunkusage_set.filter(day__gte=last_month).order_by('-day')
    if splunk.count():
        size = splunk.aggregate(db.Sum('size'))['size__sum'] or 0
        cost += splunk[0].get_price(size=size)
    return cost


def get_device_chassis_price(device):
    """
    Part of the chassis price that should be added to the blade
    server's price.
    """
    if (device.model and device.model.group and device.model.group.slots and
        device.parent and device.parent.model and device.parent.model.group and
        device.parent.model.group.slots):
        chassis_price = (device.model.group.slots * get_device_raw_price(device.parent) /
                         device.parent.model.group.slots)
    else:
        chassis_price = 0
    return chassis_price


def get_device_virtuals_price(device):
    """Calculate the total price of all virtual servers inside."""

    price = math.fsum(
        get_device_price(dev) for dev in
        device.child_set.filter(model__type=DeviceType.virtual_server.id))
    return price


def get_device_virtual_cpu_price(device):
    """Calculate the price of a single virtual cpu for virtual servers inside."""

    cpu_price = get_device_cpu_price(device)
    total_virtual_cpus = Processor.objects.filter(
            device__parent=device,
            device__model__type=DeviceType.virtual_server.id
        ).count()
    if not total_virtual_cpus:
        return 0
    return (cpu_price or 0) / total_virtual_cpus


def get_device_cpu_price(device):
    if (device.parent and device.model and
        device.model.type == DeviceType.virtual_server.id):
        # Virtual servers count CPU price based on the price of the hypervisor
        total_cpus = device.processor_set.count()
        return get_device_virtual_cpu_price(device.parent) * total_cpus
    # Non-virtual servers just sum the prices of individual CPUs
    price = math.fsum(cpu.get_price() for cpu in device.processor_set.all())
    if not price and device.model and device.model.type in {
            DeviceType.rack_server.id, DeviceType.blade_server.id}:
        # Fall back to OperatingSystem-visible cores, and then to default
        try:
            os = OperatingSystem.objects.get(device=device)
            group = ComponentModelGroup.objects.get(name='OS Detected CPU')
        except (OperatingSystem.DoesNotExist, ComponentModelGroup.DoesNotExist):
            pass
        else:
            if os.cores_count:
                return os.cores_count * group.price
        try:
            group = ComponentModelGroup.objects.get(name='Default CPU')
        except ComponentModelGroup.DoesNotExist:
            pass
        else:
            return group.price
    return price


def get_device_memory_price(device):
    price = math.fsum(
        m.get_price() for m in device.memory_set.all() if m.model)
    if not price and device.model and device.model.type in (
        DeviceType.rack_server.id, DeviceType.blade_server.id,
        DeviceType.virtual_server.id):
        try:
            os = OperatingSystem.objects.get(device=device)
            group = ComponentModelGroup.objects.get(name='OS Detected Memory')
        except (OperatingSystem.DoesNotExist, ComponentModelGroup.DoesNotExist):
            pass
        else:
            if not group.per_size:
                return group.price or 0
            if os.memory:
                return (os.memory /
                        (group.size_modifier or 1)) * (group.price or 0)
        try:
            group = ComponentModelGroup.objects.get(name='Default Memory')
        except ComponentModelGroup.DoesNotExist:
            pass
        else:
            return group.price
    return price


def get_device_local_storage_price(device):
    price = math.fsum(s.get_price() for s in device.storage_set.all())
    if not price and device.model and device.model.type in (
            DeviceType.rack_server.id, DeviceType.blade_server.id,
            DeviceType.virtual_server.id):
        try:
            os = OperatingSystem.objects.get(device=device)
            group = ComponentModelGroup.objects.get(name='OS Detected Storage')
        except (OperatingSystem.DoesNotExist, ComponentModelGroup.DoesNotExist):
            pass
        else:
            if not group.per_size:
                return group.price or 0
            else:
                storage = os.storage or 0
                remote_storage_size = math.fsum(
                    m.get_size() for m in device.disksharemount_set.all()
                )
                storage -= remote_storage_size
                if storage > 0:
                    return (storage /
                            (group.size_modifier or 1)) * (group.price or 0)
        if device.model.type != DeviceType.virtual_server.id:
            try:
                group = ComponentModelGroup.objects.get(name='Default Disk')
            except ComponentModelGroup.DoesNotExist:
                pass
            else:
                return group.price
    return price


def get_device_exported_storage_price(device):
    return math.fsum(
        s.get_price() for s in device.diskshare_set.all()
            if s.disksharemount_set.exclude(device=None).count()
    )


def get_device_components_price(device):
    return math.fsum(c.get_price() for c in device.genericcomponent_set.all())


def get_device_fc_price(device):
    return math.fsum(fc.get_price() for fc in device.fibrechannel_set.all())


def get_device_software_price(device):
    return math.fsum(s.get_price() for s in device.software_set.all())


def get_device_operatingsystem_price(device):
    return math.fsum(os.get_price() for os in device.operatingsystem_set.all())


def get_device_auto_price(device):
    """Calculate the total price of all components."""

    model_price = (device.model.group.price or 0) if (
                    device.model and device.model.group) else 0
    return math.fsum([
        model_price,
        get_device_memory_price(device),
        get_device_cpu_price(device),
        get_device_local_storage_price(device),
        get_device_components_price(device),
        get_device_fc_price(device),
        get_device_software_price(device),
        get_device_operatingsystem_price(device),
    ])


def device_update_cached(device):
    stack = [device]
    devices = [device]
    visited = {device}
    while stack:
        device = stack.pop()
        devices.append(device)
        for d in device.child_set.all():
            if d in visited:
                # Make sure we don't do the same device twice.
                continue
            visited.add(d)
            stack.append(d)
    devices.reverse() # Do the children before their parent.
    for d in devices:
        d.name = device.get_name()
        d.cached_price = get_device_price(d)
        d.cached_cost = get_device_cost(d)
        d.save()


def details_dev(dev, purchase_only=False):
    yield {
        'label': 'Device',
        'model': dev.model,
        'serial': dev.sn,
        'price': dev.price or dev.model.get_price() if dev.model else 0,
        'href': '/admin/discovery/device/%d/' % dev.id,
    }
    if purchase_only:
        return
    if dev.model is None:
        return
    if dev.model.type == DeviceType.blade_system.id:
        for d in dev.child_set.all():
            if d.model.type == DeviceType.blade_server.id:
                chassis_price = get_device_chassis_price(d)
                if chassis_price:
                    yield {
                        'label': escape('Blade server %s' % d.name),
                        'model': d.model,
                        'price': -chassis_price,
                        'icon': 'fugue-server-medium',
                        'serial': d.sn,
                    }
            else:
                yield {
                    'label': d.name,
                    'model': d.model,
                    'serial': d.sn,
                }
    elif dev.model.type == DeviceType.blade_server.id:
        chassis_price = get_device_chassis_price(dev)
        if chassis_price:
            yield {
                'label': '%s/%s of chassis' % (dev.model.group.slots,
                                              dev.parent.model.group.slots),
                'model': dev.parent.model,
                'price': chassis_price,
                'icon': 'fugue-servers',
                'serial': dev.parent.sn,
                'href': '/admin/discovery/device/%d/' % dev.parent.id,
            }


def details_cpu(dev, purchase_only=False):
    has_cpu = False
    if dev.parent and dev.model and dev.model.type == DeviceType.virtual_server.id:
        cpu_price = get_device_virtual_cpu_price(dev.parent)
        for cpu in dev.processor_set.all():
            has_cpu = True
            yield {
                'label': cpu.label,
                'price': cpu_price,
                'model_name': 'Virtual CPU',
                'icon': 'fugue-processor',
            }
    else:
        for cpu in dev.processor_set.all():
            has_cpu = True
            speed = cpu.model.speed if (cpu.model and
                                        cpu.model.speed) else cpu.speed
            yield {
                'label': cpu.label,
                'model': cpu.model,
                'size': '%d core(s)' % cpu.get_cores(),
                'speed': '%d Mhz' % speed if speed else None,
                'price': cpu.get_price(),
            }
    if purchase_only:
        return
    if not has_cpu and dev.model and dev.model.type in (
        DeviceType.blade_server.id, DeviceType.rack_server.id,
        DeviceType.virtual_server.id):
        try:
            os = OperatingSystem.objects.get(device=dev)
            group = ComponentModelGroup.objects.get(name='OS Detected CPU')
            for core_num in xrange(os.cores_count or 0):
                yield {
                    'label': '%s %d' % (group.name, core_num + 1),
                    'price': group.price,
                    'icon': 'fugue-processor',
                }
        except (OperatingSystem.DoesNotExist, ComponentModelGroup.DoesNotExist):
            try:
                group = ComponentModelGroup.objects.get(name='Default CPU')
            except ComponentModelGroup.DoesNotExist:
                pass
            else:
                yield {
                    'label': group.name,
                    'price': group.price,
                    'icon': 'fugue-prohibition-button',
                }


def details_mem(dev, purchase_only=False):
    has_mem = False
    for mem in dev.memory_set.all():
        has_mem = True
        speed = mem.model.speed if (mem.model and
                                    mem.model.speed) else mem.speed
        yield {
            'label': mem.label,
            'model': mem.model,
            'size': '%d MiB' % mem.get_size(),
            'speed': '%d Mhz' % speed if speed else None,
            'price': mem.get_price(),
        }
    if purchase_only:
        return
    if not has_mem and dev.model and dev.model.type in (
        DeviceType.blade_server.id, DeviceType.rack_server.id,
        DeviceType.virtual_server.id):
        try:
            os = OperatingSystem.objects.get(device=dev)
            group = ComponentModelGroup.objects.get(name='OS Detected Memory')
            if group.per_size:
                price = "%s %s / %s %s" % (group.price, settings.CURRENCY,
                                           group.size_modifier, group.size_unit)
            else:
                price = group.price
            yield {
                'label': group.name,
                'icon': 'fugue-memory',
                'size': os.memory,
                'price': price,
            }
        except (OperatingSystem.DoesNotExist, ComponentModelGroup.DoesNotExist):
            try:
                group = ComponentModelGroup.objects.get(name='Default Memory')
            except ComponentModelGroup.DoesNotExist:
                pass
            else:
                yield {
                    'label': group.name,
                    'price': group.price,
                    'icon': 'fugue-prohibition-button',
                }


def details_disk(dev, purchase_only=False):
    has_disk = False
    for disk in dev.storage_set.all():
        if disk.model:
            has_disk = True
            size = '%d MiB' % disk.get_size()
            if disk.model and disk.model.group:
                g = disk.model.group
                if g.per_size:
                    size = '%.1f %s' % (float(disk.get_size()) /
                        (g.size_modifier or 1),
                        g.size_unit or '')
            yield {
                'label': disk.label,
                'model': disk.model,
                'serial': disk.sn or '',
                'size': size,
                'price': disk.get_price(),
            }
    for mount in dev.disksharemount_set.all():
        total = mount.get_total_mounts()
        if mount.size:
            name = '%s (%d of %d MiB)' % (
                    mount.share.label,
                    mount.size, mount.share.size)
        elif total > 1:
            name = '%s (1/%d of %d MiB)' % (
                    mount.share.label,
                    total, mount.share.size)
        else:
            name = '%s (%d MiB)' % (
                    mount.share.label,
                    mount.share.size)
        yield {
            'label': name,
            'model': mount.share.model,
            'size': mount.get_size(),
            'serial': mount.share.wwn,
            'count': total,
            'price': mount.get_price(),
            'href': '/admin/discovery/diskshare/%d/' % mount.share.id,
        }
    if purchase_only:
        return
    if not has_disk and dev.model and dev.model.type in (
            DeviceType.blade_server.id, DeviceType.rack_server.id):
        try:
            group = ComponentModelGroup.objects.get(name='Default Disk')
        except ComponentModelGroup.DoesNotExist:
            pass
        else:
            yield {
                'label': group.name,
                'price': group.price,
                'icon': 'fugue-prohibition-button',
            }
    # Exported shares
    for share in dev.diskshare_set.order_by('label').all():
        count = share.disksharemount_set.exclude(device=None).count()
        if share.disksharemount_set.exclude(
                server=dev
            ).exclude(
                server=None
            ).count():
            icon = 'fugue-globe-share'
        elif not share.full:
            icon = 'fugue-databases'
        else:
            icon = 'fugue-database'
        yield {
            'label': share.label,
            'size': share.get_total_size(),
            'price':-share.get_price() if count else 0,
            'count': count,
            'model': share.model,
            'serial': share.wwn,
            'icon': icon,
            'href': '/admin/discovery/diskshare/%d/' % share.id,
        }
    # Exported network shares
    for mount in dev.servermount_set.distinct().values(
            'volume', 'share', 'size'):
        share = DiskShare.objects.get(pk=mount['share'])
        yield {
            'label': mount['volume'] or share.label,
            'size': mount['size'] or share.get_total_size(),
            'price': 0,
            'count': share.disksharemount_set.exclude(device=None).count(),
            'serial': share.wwn,
            'model': share.model,
            'icon': 'fugue-globe-share',
            'href': '/admin/discovery/diskshare/%d/' % share.id,
        }


def details_other(dev, purchase_only=False):
    for fc in dev.fibrechannel_set.all():
        if fc.model:
            yield {
                'label': fc.label,
                'model': fc.model,
                'serial': fc.physical_id,
            }
    for c in dev.genericcomponent_set.order_by('model', 'label').all():
        if c.model:
            yield {
                'label': c.label,
                'model': c.model,
                'serial': c.sn,
                'price': c.get_price(),
                'href': '/admin/discovery/genericcomponent/%d/' % c.id,
            }
    for eth in dev.ethernet_set.order_by('label'):
        yield {
            'label': eth.label,
            'model_name': 'Speed %s' % EthernetSpeed.NameFromID(eth.speed),

            'serial': eth.mac,
            'icon': 'fugue-network-ethernet',
        }
    for soft in dev.software_set.order_by('path'):
        yield {
            'label': soft.label,
            'model': soft.model,
            'serial': soft.sn,
        }
    for os in dev.operatingsystem_set.order_by('label'):
        details = []
        if os.cores_count:
            details.append('cores count: %d' % os.cores_count)
        if os.memory:
            details.append('memory: %s MiB' % os.memory)
        if details:
            label = "%s (%s)" % (os.label, ', '.join(details))
        else:
            label = os.label
        yield {
            'label': label,
            'model': os.model,
        }


def details_all(dev, purchase_only=False):
    for detail in details_dev(dev, purchase_only):
        detail['group'] = 'dev'
        yield detail
    for detail in details_cpu(dev, purchase_only):
        detail['group'] = 'cpu'
        yield detail
    for detail in details_mem(dev, purchase_only):
        detail['group'] = 'mem'
        yield detail
    for detail in details_disk(dev, purchase_only):
        detail['group'] = 'disk'
        yield detail
    for detail in details_other(dev, purchase_only):
        detail['group'] = 'other'
        yield detail

