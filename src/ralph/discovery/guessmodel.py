#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Heuristics for guessing which plugins to try.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

def guessmodel(http_family='', snmp_name='', guessmodel=('', ''), *args, **kwargs):
    if guessmodel and guessmodel[0] or guessmodel[1]:
        return guessmodel
    if http_family in ('F5', 'HP', 'Cisco', 'Thomas-Krenn', 'Sun', 'IBM',
                       'Proxmox', 'APC', 'VTL'):
        return http_family, ''
    if http_family == 'Modular':
        return 'Intel', 'Modular'
    if http_family == 'SSG':
        return 'Cisco', 'SSG'
    if http_family == 'sscccc':
        return 'Onstor', ''
    if http_family == 'WindRiver-WebServer' or 'StorageWorks' in snmp_name:
        return 'HP', 'StorageWorks'
    if 'Onboard Administrator' in snmp_name:
        return 'HP', 'Onboard Administrator'
    if 'xen' in snmp_name:
        return '', 'XEN'
    for prefix in ('HP', 'IBM', 'Cisco', 'APC', 'Codian', '3PAR'):
        if snmp_name.startswith(prefix):
            return prefix, ''
    if snmp_name.lower().startswith('sunos'):
        return 'Sun', ''
    elif snmp_name.lower().startswith('hardware:') and 'Windows' in snmp_name:
        return 'Microsoft', 'Windows'
    elif snmp_name.lower().startswith('vmware esx'):
        return 'VMware', 'ESX'
    elif snmp_name.startswith('IronPort'):
        return 'IronPort', ''
    elif snmp_name.startswith('Intel Modular'):
        return 'Intel', 'Modular'
    elif 'Software:UCOS' in snmp_name:
        return 'Cisco', 'UCOS'
    elif 'fibre channel switch' in snmp_name.lower() or 'san switch module' in snmp_name.lower():
        return '', 'FC Switch'
    elif 'ethernet switch module' in snmp_name.lower():
        return '', 'Switch'
    if snmp_name.startswith('ProCurve'):
        return 'HP', 'ProCurve'
    elif '.f5app' in snmp_name:
        return 'F5', ''
    elif 'StorageWorks' in snmp_name:
        return 'HP', 'StorageWorks'
    elif 'linux' in snmp_name.lower():
        return '', 'Linux'
    return '', ''
