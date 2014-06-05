# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def _shares_in_results(data):
    return False


def run_job(ip, **kwargs):
    http_family = ip.http_family or ''
    if http_family not in ('Unspecified',):
        return  # It is not 3PAR.
    snmp_name = ip.snmp_name or ''
    if not snmp_name.startswith('3PAR'):
        return  # It is not 3PAR.
    data = kwargs.get('plugins_results', {})
    if not _shares_in_results(data):
        return  # No reason to run it.
