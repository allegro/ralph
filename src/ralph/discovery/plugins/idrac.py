#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import subprocess
import os
import ssl
from sys import stdout


from django.conf import settings
from ralph.util import plugin
from tempfile import mkstemp


IDRAC_USER = settings.IDRAC_USER
IDRAC_PASSWORD = settings.IDRAC_USER
SCHEMA = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2"


class IDRAC(object):
    def __init__(self, host, user=IDRAC_USER, password=IDRAC_PASSWORD):
        self.host = host
        self.user = user
        self.password = password

    def _get_cert(self):
        return 'cert'
        (handle, path) = mkstemp()
        cert = ssl.get_server_certificate((self.host, 443))
        os.write(handle, cert)
        os.close(handle)
        return path

    def _run_command(self, class_name, namespace):
        command = [
            "wsman-emu", "enumerate", "%s/%s" % (SCHEMA, class_name),
            "-N", namespace, "-u", self.user, "-p", self.password,
            "-h", self.host, "-P", '443', "-v", "-j", "urf-8",
            "-y", "basic", "-o" "-m", '256', "-V", "-c", self._get_cert(),
        ]
        print(' '.join(command))
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()
        # todo - errors handling
        return out

    def get_cpu(self):
        pass

    def get_memory(self):
        pass

    # get...


def _run_idrac(ip):
    x = IDRAC(host=ip)
    cert_filename = x._get_cert()
    output = x._run_command('DCIM_NICView', 'root/dcim')


@plugin.register(chain='discovery', requires=['ping', 'http'])
def idrac(**kwargs):
    if not IDRAC_USER or not IDRAC_PASSWORD:
        return False, "not configured", kwargs
    ip = str(kwargs['ip'])
    http_family = kwargs.get('http_family')
    if http_family not in ('Dell', ):
        return False, 'no match', kwargs
    name = _run_idrac(ip)
    return True, name, kwargs

