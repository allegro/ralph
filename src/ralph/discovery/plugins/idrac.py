#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ssl
import subprocess

from django.conf import settings
from tempfile import mkstemp
from xml.etree import cElementTree as ET

from ralph.util import plugin


IDRAC_USER = settings.IDRAC_USER
IDRAC_PASSWORD = settings.IDRAC_PASSWORD

SCHEMA = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2"
XMLNS_S = "{http://www.w3.org/2003/05/soap-envelope}"
XMLNS_WSEN = "{http://schemas.xmlsoap.org/ws/2004/09/enumeration}"
XMLNS_WSMAN = "{http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd}"
XMLNS_N1_BASE = "{http://schemas.dell.com/wbem/wscim/1/cim-schema/2/%s}"


class IDRAC(object):
    def __init__(self, host, user=IDRAC_USER, password=IDRAC_PASSWORD):
        self.host = host
        self.user = user
        self.password = password

    def _get_cert(self):
        (handle, path) = mkstemp()
        cert = ssl.get_server_certificate((self.host, 443))
        os.write(handle, cert)
        os.close(handle)
        return path

    def _run_command(self, class_name, namespace='root/dcim'):
        command = [
            "wsman", "enumerate", "%s/%s" % (SCHEMA, class_name),
            "-N", namespace, "-u", self.user, "-p", self.password,
            "-h", self.host, "-P", "443", "-v", "-j", "utf-8",
            "-y", "basic", "-o", "-m", "256", "-V", "-c", self._get_cert(),
        ]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()
        # todo - errors handling
        return unicode(out, 'utf-8', 'replace')

    def get_base_info(self):
        soap_result = self._run_command('DCIM_SystemView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_SystemView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_SystemView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        record = tree.findall(q)[0]
        result = {
            'manufacturer': record.find(
                "{}{}".format(xmlns_n1, 'Manufacturer')
            ).text,
            'model': record.find(
                "{}{}".format(xmlns_n1, 'Model')
            ).text,
            'sn': record.find(
                "{}{}".format(xmlns_n1, 'BoardSerialNumber')
            ).text

        }
        return result

    def get_ethernets(self):
        soap_result = self._run_command('DCIM_NICView')
        tree = ET.XML(soap_result)
        xmlns_n1 = XMLNS_N1_BASE % "DCIM_NICView"
        q = "{}Body/{}EnumerateResponse/{}Items/{}DCIM_NICView".format(
            XMLNS_S,
            XMLNS_WSEN,
            XMLNS_WSMAN,
            xmlns_n1
        )
        results = []
        for record in tree.findall(q):
            results.append({
                'mac': record.find(
                    "{}{}".format(xmlns_n1, 'CurrentMACAddress')
                ).text,
                'label': record.find(
                    "{}{}".format(xmlns_n1, 'ProductName')
                ).text,

            })
        return results

    def get_cpu(self):
        pass

    def get_memory(self):
        pass


def _run_idrac(ip):
    idrac = IDRAC(ip)
    #base_info = idrac.get_base_info()
    #print(base_info)
    eth = idrac.get_ethernets()
    print(eth)


@plugin.register(chain='discovery', requires=['ping', 'http'])
def idrac(**kwargs):
    if not IDRAC_USER or not IDRAC_PASSWORD:
        return False, "not configured", kwargs
    ip = str(kwargs['ip'])
    http_family = kwargs.get('http_family')
    if http_family not in ('Mbedthis-Appweb', ):
        return False, 'no match', kwargs
    name = _run_idrac(ip)
    return True, name, kwargs

