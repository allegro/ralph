# -*- coding: utf-8 -*-

"""
Set of usefull functions to retrieve data from Puppet facts.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import re
import logging

from lck.django.common.models import MACAddressField

from ralph.discovery.hardware import normalize_wwn
from ralph.discovery.models import (
    DISK_PRODUCT_BLACKLIST,
    DISK_VENDOR_BLACKLIST,
    DeviceType,
    MAC_PREFIX_BLACKLIST,
    SERIAL_BLACKLIST,
)
from ralph.discovery.models_component import cores_from_model
from ralph.scan.lshw import parse_lshw, handle_lshw_storage
from ralph.scan.lshw import Error as LshwError
from ralph.util import network, uncompress_base64_data, units


logger = logging.getLogger("SCAN")


SMBIOS_BANNER = 'ID    SIZE TYPE'
DENSE_SPEED_REGEX = re.compile(r'(\d+)\s*([GgHhKkMmZz]+)')
_3WARE_GENERAL_REGEX = re.compile(r'tw_([^_]+_[^_]+)_([^_]+)')
SMARTCTL_REGEX = re.compile(r'smartctl_([^_]+)__(.+)')
HPACU_GENERAL_REGEX = re.compile(r'hpacu_([^_]+)__(.+)')
HPACU_LOGICAL_PHYSICAL_REGEX = re.compile(r'([^_]+)__(.+)')
MEGARAID_REGEX = re.compile(r'megacli_([^_]+)_([^_]+)__(.+)')
INQUIRY_REGEXES = (
    re.compile(
        r'^(?P<vendor>OCZ)-(?P<sn>[a-zA-Z0-9]{16})OCZ-(?P<product>\S+)\s+.*$'),
    re.compile(
        r'^(?P<vendor>(FUJITSU|TOSHIBA))\s+(?P<product>[a-zA-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]{16})$'),
    re.compile(
        r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[^G]+G)(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[0-9]+SS)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<vendor>SEAGATE)\s+(?P<product>ST[A-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<sn>[a-zA-Z0-9]{18})\s+(?P<vendor>INTEL)\s+(?P<product>[a-zA-Z0-9]+)\s+.*$'),
    re.compile(
        r'^(?P<vendor>IBM)-(?P<product>[a-zA-Z0-9]+)\s+(?P<sn>[a-zA-Z0-9]+)$'),
    re.compile(
        r'^(?P<vendor>HP)\s+(?P<product>[a-zA-Z0-9]{11})\s+(?P<sn>[a-zA-Z0-9]{12})$'),
    re.compile(
        r'^(?P<vendor>HITACHI)\s+(?P<product>[a-zA-Z0-9]{15})(?P<sn>[a-zA-Z0-9]{15})$'),
    re.compile(
        r'^(?P<vendor>HITACHI)\s+(?P<product>[a-zA-Z0-9]{15})\s+(?P<sn>[a-zA-Z0-9]{12})$'),
    re.compile(
        r'^(?P<sn>[a-zA-Z0-9]{15})\s+(?P<vendor>Samsung)\s+(?P<product>[a-zA-Z0-9\s]+)\s+.*$'),
    re.compile(
        r'^(?P<vendor>WD)\s+(?P<product>WD[A-Z0-9]{8})\s+(?P<sn>[a-zA-Z0-9]{16})$'),
)
SEPARATE_VERSION = re.compile('[~|+|\-]')


def handle_facts(facts, is_virtual=False):
    """
    Handle all facts and return standardized device info.
    """

    results = {}
    if is_virtual:
        results['model_name'] = " ".join(
            (facts['manufacturer'], facts['virtual']),
        )
        results['type'] = DeviceType.virtual_server.raw
        mac_address = handle_default_mac_address(facts)
        if mac_address:
            results['mac_addresses'] = [mac_address]
        sn = "".join(
            (
                "VIRT0_",
                mac_address,
                '_',
                hashlib.md5(
                    facts.get(
                        'sshdsakey',
                        facts.get('sshrsakey', '#'),
                    ),
                ).hexdigest()[:8],
            ),
        )
    else:
        sn = facts.get('serialnumber')
        if sn in SERIAL_BLACKLIST:
            sn = None
        prod_name = facts.get('productname')
        manufacturer = facts.get('manufacturer')
        if prod_name:
            if manufacturer and manufacturer in prod_name:
                model_name = prod_name
            else:
                model_name = "{} {}".format(manufacturer, prod_name)
            results['model_name'] = model_name
            if DeviceType.blade_server.matches(model_name):
                model_type = DeviceType.blade_server
            else:
                model_type = DeviceType.rack_server
            results['type'] = model_type.raw
    if sn:
        results['serial_number'] = sn
    mac_addresses = handle_facts_mac_addresses(facts)
    if mac_addresses:
        if 'mac_addresses' in results:
            results['mac_addresses'].extend(mac_addresses)
        else:
            results['mac_addresses'] = mac_addresses
    if 'smbios' in facts:
        processors, memory = handle_facts_smbios(facts['smbios'], is_virtual)
        if processors:
            results['processors'] = processors
        if memory:
            results['memory'] = memory
    disks = handle_facts_disks(facts)
    if disks:
        results['disks'] = disks
    return results


def handle_default_mac_address(facts):
    for suffix in ('', '_eth0', '_igb0', '_bnx0', '_bge0', '_nfo0', '_nge0'):
        mac = facts.get('macaddress{}'.format(suffix))
        if mac:
            try:
                result = MACAddressField.normalize(mac)
            except ValueError:
                continue
            if result[:6] in MAC_PREFIX_BLACKLIST:
                continue
            return result


def handle_facts_mac_addresses(facts):
    mac_addresses = set()
    for interface in facts['interfaces'].split(','):
        mac_address = facts.get('macaddress_{}'.format(interface))
        if not mac_address:
            continue
        mac_addresses.add(MACAddressField.normalize(mac_address))
    return list(mac_addresses)


def handle_facts_ip_addresses(facts):
    ip_addresses = set()
    for interface in facts['interfaces'].split(','):
        try:
            ip = network.validate_ip(facts['ipaddress_{}'.format(interface)])
            ip_addresses.add(ip)
        except (ValueError, KeyError):
            pass
    return list(ip_addresses)


def handle_facts_smbios(fact_smbios, is_virtual):
    raw_smbios = uncompress_base64_data(fact_smbios)
    smbios = _parse_smbios(raw_smbios)
    detected_memory = []
    for memory_chip in smbios.get('MEMDEVICE', ()):
        try:
            size, size_units = memory_chip.get('Size', '').split(' ', 1)
            size = int(size)
            size /= units.size_divisor[size_units]
            size = int(size)
        except ValueError:
            continue  # empty slot
        for split_key in ('BANK', 'Slot '):
            try:
                bank = memory_chip.get('Bank Locator').split(split_key)[1]
                bank = int(bank) + 1
                break
            except (IndexError, ValueError):
                bank = None  # unknown bank
        if bank is None:
            continue
        detected_memory.append({
            'label': "{}{} {}".format(
                'Virtual ' if is_virtual else '',
                memory_chip.get(
                    'Device Locator',
                    memory_chip.get('Location Tag', 'DIMM'),
                ),
                memory_chip.get('Part Number', ''),
            ),
            'size': size,
        })
    detected_cpus = []
    for cpu in smbios.get('PROCESSOR', ()):
        m = DENSE_SPEED_REGEX.match(cpu.get('Maximum Speed', ''))
        if not m:
            continue
        if 'enabled' not in cpu.get('Processor Status', ''):
            continue
        speed = int(m.group(1))
        speed_units = m.group(2)
        speed /= units.speed_divisor[speed_units]
        speed = int(speed)
        label = cpu['Location Tag']
        family = cpu['Family']
        if '(other)' in family:
            family = cpu['Manufacturer']
        index_parts = []
        for cpu_part in cpu['Location Tag'].replace('CPU', '').split():
            try:
                index_parts.append(int(cpu_part.strip()))
            except ValueError:
                continue
        index = reduce(lambda x, y: x * y, index_parts)
        model_name = " ".join(cpu.get('Version', family).split())
        detected_cpus.append({
            'model_name': model_name,
            'speed': speed,
            'cores': max(1, cores_from_model(model_name)),
            'family': family,
            'label': label,
            'index': index,
        })
    return detected_cpus, detected_memory


def _parse_smbios(raw_smbios):
    if not raw_smbios.startswith(SMBIOS_BANNER):
        raise ValueError("Incompatible SMBIOS answer.")
    smb = {}
    current = None
    for line in raw_smbios.split('\n'):
        if line == SMBIOS_BANNER:
            if current:
                ctype = current['__TYPE__']
                del current['__TYPE__']
                smb.setdefault(ctype, []).append(current)
                current = None
        elif current is None:
            for token in line.split():
                if token.startswith('SMB_TYPE_'):
                    current = {'__TYPE__': token[9:]}
                    break
        else:
            if ':' in line:
                key, value = line.split(':', 1)
                current[key.strip()] = value.strip()
            else:
                current.setdefault('capabilities', []).append(line)
    return smb


def handle_facts_disks(facts):
    disks = {}
    _cur_key = None
    for k, v in facts.iteritems():
        if not k.startswith('disk_'):
            continue
        k = k[5:]
        if k.endswith('_product'):
            _cur_key = 'product'
            k = k[:-8]
        elif k.endswith('_revision'):
            _cur_key = 'revision'
            k = k[:-9]
        elif k.endswith('_size'):
            _cur_key = 'size'
            k = k[:-5]
        elif k.endswith('_vendor'):
            _cur_key = 'vendor'
            k = k[:-7]
        elif k.endswith('_serial'):
            _cur_key = 'serial'
            k = k[:-7]
        else:
            continue
        disks.setdefault(k, {})[_cur_key] = v.strip()
    detected_disks = []
    for mount_point, disk in disks.iteritems():
        try:
            if 'size' not in disk or not int(disk['size']):
                continue
        except ValueError:
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        sn = disk.get('serial', '').strip()
        detected_disk = {
            'size': int(int(disk['size']) / 1024 / 1024),
            'label': '{} {} {}'.format(
                disk['vendor'].strip(), disk['product'].strip(),
                disk['revision'].strip(),
            ),
            'mount_point': mount_point,
            'family': disk['vendor'].strip(),
        }
        if sn:
            detected_disk['serial_number'] = sn
        detected_disks.append(detected_disk)
    return detected_disks


def handle_facts_wwn(facts):
    disk_shares = []
    for key, wwn in facts.iteritems():
        if not key.startswith('wwn_mpath'):
            continue
        path = key.replace('wwn_', '')
        disk_shares.append({
            'serial_number': normalize_wwn(wwn),
            'volume': '/dev/mapper/%s' % path,

        })
    return disk_shares


def handle_facts_3ware_disks(facts):
    disks = {}
    for k, value in facts.iteritems():
        m = _3WARE_GENERAL_REGEX.match(k)
        if not m:
            continue
        key = m.group(2)
        physical_disk = m.group(1)
        disks.setdefault(physical_disk, {})[key] = value.strip()
    detected_disks = []
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial'):
            continue
        size_value, size_unit, _ = disk['capacity'].split(None, 2)
        size = int(float(size_value) / units.size_divisor[size_unit])
        detected_disk = {
            'serial_number': disk['serial'],
            'size': size,
            'label': disk['model'],
            'family': disk['model'],
        }
        detected_disks.append(detected_disk)
    return detected_disks


def handle_facts_smartctl(facts):
    disks = {}
    for k, value in facts.iteritems():
        m = SMARTCTL_REGEX.match(k)
        if not m:
            continue
        disk = m.group(1)
        property = m.group(2)
        disks.setdefault(disk, {})[property] = value.strip()
    detected_disks = []
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial_number') or disk.get('device_type') != 'disk':
            continue
        if {
            'user_capacity', 'vendor', 'product', 'transport_protocol',
        } - set(disk.keys()):
            # not all required keys present
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        size_value, size_unit, rest = disk['user_capacity'].split(' ', 2)
        size_value = size_value.replace(',', '')
        label_meta = [' '.join(disk['vendor'].split()), disk['product']]
        if 'transport_protocol' in disk:
            label_meta.append(disk['transport_protocol'])
        family = disk['vendor'].strip() or 'Generic disk'
        detected_disks.append({
            'serial_number': disk['serial_number'],
            'size': int(int(size_value) / units.size_divisor[size_unit]),
            'label': ' '.join(label_meta),
            'family': family,
        })
    return detected_disks


def handle_facts_hpacu(facts):
    disks = {}
    for k, value in facts.iteritems():
        m = HPACU_GENERAL_REGEX.match(k)
        if not m:
            continue
        n = HPACU_LOGICAL_PHYSICAL_REGEX.match(m.group(2))
        physical_disk = n.group(1) if n else None
        property = n.group(2) if n else m.group(2)
        if not physical_disk:
            continue
        disks.setdefault(physical_disk, {})[property] = value.strip()
    detected_disks = []
    for disk_handle, disk in disks.iteritems():
        if not disk.get('serial_number'):
            continue
        size_value, size_unit = disk['size'].split()
        detected_disks.append({
            'serial_number': disk['serial_number'],
            'label': '{} {}'.format(
                ' '.join(disk['model'].split()),
                disk['interface_type'],
            ),
            'size': int(float(size_value) / units.size_divisor[size_unit]),
            'family': ' '.join(disk['model'].split()),
        })
    return detected_disks


def _handle_inquiry_data(raw, controller, disk):
    for regex in INQUIRY_REGEXES:
        m = regex.match(raw)
        if m:
            return m.group('vendor'), m.group('product'), m.group('sn')
    raise ValueError(
        "Incompatible inquiry_data for disk {}/{}: {}".format(
            controller, disk, raw,
        )
    )


def handle_facts_megaraid(facts):
    disks = {}
    for k, value in facts.iteritems():
        m = MEGARAID_REGEX.match(k)
        if not m:
            continue
        controller = m.group(1)
        disk = m.group(2)
        property = m.group(3)
        disks.setdefault((controller, disk), {})[property] = value.strip()
    detected_disks = []
    for (controller_handle, disk_handle), disk in disks.iteritems():
        try:
            disc_data = _handle_inquiry_data(
                disk.get('inquiry_data', ''),
                controller_handle,
                disk_handle,
            )
        except ValueError:
            logger.warning("Unable to parse disk {}".format(disk))
            continue
        disk['vendor'], disk['product'], disk['serial_number'] = disc_data
        if not disk.get('serial_number') or disk.get('media_type') not in (
            'Hard Disk Device', 'Solid State Device',
        ):
            continue
        if {
            'coerced_size', 'vendor', 'product', 'pd_type',
        } - set(disk.keys()):
            # not all required keys present
            continue
        if disk['vendor'].lower() in DISK_VENDOR_BLACKLIST:
            continue
        if disk['product'].lower() in DISK_PRODUCT_BLACKLIST:
            continue
        size_value, size_unit, rest = disk['coerced_size'].split(' ', 2)
        size_value = size_value.replace(',', '')
        label_meta = [' '.join(disk['vendor'].split()), disk['product']]
        if 'pd_type' in disk:
            label_meta.append(disk['pd_type'])
        detected_disks.append({
            'serial_number': disk['serial_number'],
            'label': ' '.join(label_meta),
            'size': int(float(size_value) / units.size_divisor[size_unit]),
            'family': ' '.join(disk['vendor'].split()),
        })
    return detected_disks


def _get_storage_size_from_facts(facts):
    disk_size = 0
    smartctl_size = 0
    reg = re.compile(r'^[0-9][0-9,]*')
    for k, v in facts.iteritems():
        if k.startswith('smartctl_') and k.endswith('_user_capacity'):
            match = reg.match(v.strip())
            if match:
                try:
                    size = int(match.group(0).replace(',', ''))
                except ValueError:
                    pass
                else:
                    size = int(size / 1024 / 1024)
                    smartctl_size += size
        if k.startswith('disk_') and k.endswith('_size'):
            try:
                size = int(int(v.strip()) / 1024 / 1024)
            except ValueError:
                pass
            else:
                disk_size += size
    return smartctl_size if smartctl_size else disk_size


def handle_facts_os(facts, is_virtual=False):
    result = {}
    try:
        os_name = "%s %s" % (
            facts['operatingsystem'],
            facts['operatingsystemrelease'],
        )
        family = facts['kernel']
    except KeyError:
        return result
    os_version = facts.get('kernelrelease', '')
    result['system_label'] = '%s%s' % (
        os_name,
        ' %s' % os_version if os_version else '',
    )
    result['system_family'] = family
    memory_size = None
    try:
        memory_size, unit = re.split('\s+', facts['memorysize'].lower())
        if unit == 'tb':
            memory_size = int(float(memory_size) * 1024 * 1024)
        elif unit == 'gb':
            memory_size = int(float(memory_size) * 1024)
        elif unit == 'mb' or unit == 'mib':
            memory_size = int(float(memory_size))
    except (KeyError, ValueError):
        pass
    if memory_size:
        result['system_memory'] = memory_size
    cores_key = ('physical' if not is_virtual else '') + 'processorcount'
    try:
        cores_count = int(facts.get(cores_key))
    except TypeError:
        pass
    else:
        result['system_cores_count'] = cores_count
    storage_size = _get_storage_size_from_facts(facts)
    if not storage_size:
        lshw = facts.get('lshw', None)
        if lshw:
            try:
                lshw = uncompress_base64_data(lshw)
            except TypeError:
                pass
            else:
                try:
                    lshw = parse_lshw(lshw)
                except LshwError:
                    pass
                else:
                    storages = handle_lshw_storage(lshw)
                    storage_size = 0
                    for storage in storages:
                        storage_size += storage['size']
    if storage_size:
        result['system_storage'] = storage_size
    return result


def _parse_packages(facts):
    data = uncompress_base64_data(facts)
    if data:
        packages = data.strip().split(',')
        for package in packages:
            try:
                name, version = package.split(None, 1)
            except ValueError:
                continue
            yield {
                'name': name,
                'version': version,
            }


def handle_facts_packages(facts):
    packages = []
    packages_list = _parse_packages(facts.get('packages'))
    if not packages_list:
        return packages
    for package in packages_list:
        version = filter(
            None,
            SEPARATE_VERSION.split(package['version'], 1)
        )[0]
        package_name = '{} - {}'.format(package['name'], version)
        packages.append({
            'label': package['name'],
            'version': version,
            'path': package_name,
            'model_name': package_name,
        })
    return packages
