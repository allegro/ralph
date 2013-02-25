#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import time
import pprint

from django.db.transaction import commit_on_success

from ralph.util import plugin
from ralph.discovery.models import (
    ComponentModel,
    ComponentType,
    Device,
    DeviceType,
    DiskShare,
    DiskShareMount,
    FibreChannel,
    GenericComponent,
    IPAddress,
    Memory,
    OperatingSystem,
    Processor,
    Software,
    Storage,
)
# Load all the plugins.
import ralph.scan.plugins


SAVE_PRIORITY = 100


def run_chain(chain, max_retries=5, plugins=None, **kwargs):
    """Run selected plugins from a chain in the right order, and return a dict
    with their rsults. If no plugins are selected, all plugins from the chain
    are run. Plugins that raise ``plugin.Restart`` are retried up to max_retries
    times. Exceptions from plugins are caught and logged.
    """
    if plugins:
        old_plugins = set()
        while old_plugins != plugins:
            old_plugins = set(plugins)
            for requirements, name in plugin.BY_REQUIREMENTS[chain].iteritems():
                if name in plugins:
                    plugins |= requirements
    tried = set()
    successful = set()
    results = {}
    while True:
        to_run = plugin.next(chain, successful)
        if plugins:
            to_run = to_run & plugins
        if not to_run:
            break;
        plugin_name = plugin.highest_priority('scan', to_run)
        tried.add(plugin_name)
        try:
            for retry in xrange(max_retries):
                try:
                    result = plugin.run(plugin_name, results=results, **kwargs)
                except plugin.Restart:
                    time.sleep(2 ** retry)
                else:
                    break
            else:
                raise plugin.PluginFailed("Failed after %d retries." % retry)
        except plugin.PluginFailed as e:
            logging.info(str(e))
        except Exception as e:
            logging.exception(e)
        else:
            results[plugin_name] = result
            successful.add(plugin_name)
    return results


def scan_address(address, plugins=None):
    """Run a scan on a single IP address and save the results in the database.
    If a list of plugin names is provided, only those plugins are tried.
    """
    results = run_chain('scan', plugins=plugins, ip=address)
    save_results(address, results)


class PluginResultBag(object):
    """Stores data from multiple plugins and lets query it by priority."""

    NO_DEFAULT = object()

    def __init__(self, data):
        self.data = data
        self.plugins = plugin.prioritize(data.keys())

    def get(self, key, default=NO_DEFAULT):
        """Return the value from the plugin with the highest priority."""
        for name in self.plugins:
            try:
                return self.data[name][key]
            except KeyError:
                continue
        if default == self.NO_DEFAULT:
            raise KeyError()
        return default

    def get_all(self, key):
        """Return the merged lists from all plugins."""
        ret = set()
        for name in self.plugins:
            ret |= set(self.data[name].get(key, []))
        return ret


@commit_on_success
def save_results(self, address, results):
    """Analyze the results of a scan and save them to the database."""
    data = PluginResultBag(results)
    logging.debug(pprint.pformat(data))
    _save_device(data)


def _save_device(data):
    dev = Device.create(
        priority=SAVE_PRIORITY,
        sn=data.get('sn'),
        macs=data.get_all('macs'),
        model_name=data.get('model_name'),
        model_type=data.get('model_type'),
    )
    _save_memory(dev, data.get_all('memory'))
    _save_cpus(dev, data.get_all('cpus'))
    _save_disks(dev, data.get_all('disks'))
    _save_fcs(dev, data.get_all('fcs'))
    _save_exported_shares(dev, data.get_all('exported_shares'))
    _save_mounted_shares(dev, data.get_all('mounted_shares'))
    _save_components(dev, data.get_all('components'))
    _save_software(dev, data.get_all('software'))
    _save_addresses(dev, data.get_all('addresses'))
    _save_subdevices(dev, data.get_all('devices'))
    _save_system(dev, data.get('system'))
    return dev


def _save_memory(dev, memory_set):
    saved_ids = set()
    for data in memory_set:
        model, new = ComponentModel.create(
            type=ComponentType.memory,
            priority=SAVE_PRIORITY,
            size=data.get('size'),
            speed=data.get('speed'),
        )
        mem, new = Memory.objects.get_or_create(
            device=dev,
            index=data.get('index'),
        )
        mem.model = model
        mem.label = data.get('label')
        mem.size = data.get('size')
        mem.speed = data.get('speed')
        saved_ids.add(mem.id)
    for mem in Memory.objects.filter(device=dev).exclude(id__in=saved_ids):
        mem.delete()


def _save_cpus(dev, cpu_set):
    saved_ids = set()
    for data in cpu_set:
        model, new = ComponentModel.create(
            type=ComponentType.processor,
            priority=SAVE_PRIORITY,
            speed=data.get('speed'),
            cores=data.get('cores'),
            family=data.get('family'),
        )
        cpu, new = Processor.objects.get_or_create(
            index=data.get('index'),
            device=dev,
        ),
        cpu.model = model
        cpu.label = data.get('label')
        cpu.size = data.get('size')
        cpu.cores = model.cores
        cpu.speed = data.get('speed')
        cpu.save()
        saved_ids.add(cpu.id)
    for cpu in Processor.objects.filter(device=dev).exclude(id__in=saved_ids):
        cpu.delete()


def _save_disks(dev, disk_set):
    saved_ids = set()
    for data in disk_set:
        model, new = ComponentModel.create(
            type=ComponentType.processor,
            priority=SAVE_PRIORITY,
            family=data.get('family'),
            size=data.get('size'),
            speed=data.get('speed'),
        )
        if data.get('sn'):
            disk, new = Storage.obejcts.get_or_create(
                model=model,
                sn=data.get('sn'),
            )
        elif data.get('mount_point'):
            disk, new = Storage.obejcts.get_or_create(
                model=model,
                mount_point=data.get('mount_point'),
                device=dev,
            )
        else:
            continue
        disk.device = dev
        disk.label = data.get('label')
        disk.size = data.get('size')
        disk.save()
        saved_ids.add(disk.id)
    for disk in Storage.objects.filter(device=dev).exclude(id__in=saved_ids):
        disk.delete()


def _save_fcs(dev, fc_set):
    saved_ids = set()
    for data in fc_set:
        model, new = ComponentModel.create(
            type=ComponentType.fibre_channel,
            priority=SAVE_PRIORITY,
            name=data.get('model'),
        )
        fc, new = FibreChannel.objects.get_or_create(
            physcial_id=data.get('physical_id'),
        )
        fc.model = model
        fc.label = data.get('label')
        fc.device = dev
        fc.save()
        saved_ids.add(fc.id)
    for fc in FibreChannel.objects.filter(device=dev).exclude(id__in=saved_ids):
        fc.delete()


def _save_mounted_shares(dev, mount_set):
    saved_ids = set()
    for data in mount_set:
        try:
            share = DiskShare.objects.get(wwn=data['wwn'])
        except DiskShare.DoesNotExist:
            logging.error("A share with serial %r doesn't exits.", data['wwn'])
            continue
        mount, new = DiskShareMount.objects.get_or_create(
            share=share,
            device=dev,
        )
        mount.is_virtual = bool(data.get('virtual'))
        mount.server = data.get('server')
        mount.size = data.get('size')
        mount.volume = data.get('volume')
        mount.save()
        saved_ids.add(mount.id)
    for m in DiskShareMount.objects.filter(device=dev).exclude(id__in=saved_ids):
        m.delete()


def _save_exported_shares(dev, share_set):
    saved_ids = set()
    for data in share_set:
        model, new = ComponentModel.create(
            type=ComponentType.share,
            priority=SAVE_PRIORITY,
            speed=data.get('speed'),
            family=data.get('family'),
            name=data.get('name'),
        )
        share, new = DiskShare.objects.get_or_create(
            wwn=data.get('wwn'),
        )
        share.device = dev
        share.model = model
        share.label = data.get('label')
        share.size = data.get('size')
        share.snapshot_size = data.get('snapshot_size') or 0
        share.save()
        saved_ids.add(share.id)
    for share in DiskShare.objects.filter(device=dev).exclude(id__in=saved_ids):
        share.delete()


def _save_addresses(dev, address_set):
    saved_ids = set()
    for data in address_set:
        ip, new = IPAddress.objects.get_or_create(data.get('ip'))
        ip.device = dev
        ip.is_management = bool(data.get('is_management'))
        ip.save()
        saved_ids.add(ip.id)
    for ip in IPAddress.objects.filter(device=dev).exclude(id__in=saved_ids):
        ip.device = None
        ip.save()


def _save_components(dev, component_set):
    saved_ids = set()
    for data in component_set:
        model, new = ComponentModel.create(
            type=data.get('type'),
            priority=SAVE_PRIORITY,
            name=data.get('model'),
        )
        if data.get('sn'):
            component, new = GenericComponent.objects.get_or_create(
                sn=data.get('sn'),
            )
        else:
            component, new = GenericComponent.objects.get_or_create(
                model=model,
                device=dev,
            )
        component.label = data.get('label')
        component.boot_firmware = data.get('boot_firmware')
        component.hard_firmware = data.get('hard_firmware')
        component.diag_firmware = data.get('diag_firmware')
        component.mgmt_firmware = data.get('mgmt_firmware')
        component.save()
        saved_ids.add(component.id)
    for c in GenericComponent.objects.filter(device=dev).exclude(id__in=saved_ids):
        c.delete()


def _save_software(dev, software_set):
    saved_ids = set()
    for data in software_set:
        software = Software.create(
            dev=dev,
            priority=SAVE_PRIORITY,
            path=data.get('path'),
            model_name=data.get('model'),
            label=data.get('label'),
            sn=data.get('sn'),
            family=data.get('family'),
            version=data.get('version'),
        )
        software.save()
        saved_ids.add(software.id)
    for s in Software.objects.filter(device=dev).exclude(id__in=saved_ids):
        s.delete()


def _save_system(dev, data):
    if not data:
        return
    system = OperatingSystem(
        dev=dev,
        name=data['name'],
        priority=SAVE_PRIORITY,
        version=data['version'],
        memory=data['memory'],
        storage=data['storage'],
        cores_count=data['cores_count'],
        family=data['family'],
    )
    system.save()


def _save_subdevices(dev, subdevice_set):
    saved_ids = set()
    for data in subdevice_set:
        dev = _save_device(data)
        saved_ids.add(dev.id)
    if dev.model and dev.model.type in {
            DeviceType.data_center,
            DeviceType.rack,
        }:
        return
    for d in Device.objects.filter(parent=dev).exclude(id__in=saved_ids):
        d.parent = dev.parent

