#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import subprocess

from django.conf import settings
from ralph.util import plugin


IDRAC_USER = settings.IDRAC_USER
IDRAC_PASSWORD = settings.IDRAC_USER
SCHEMA = "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2"


class IDRAC(object):
    def __init__(self, host, user=IDRAC_USER, password=IDRAC_PASSWORD):
        self.host = host
        self.user = user
        self.password = password

    def _get_cert(self):
        pass

    def _run_command(self, class_name, namespace):
        command = [
            "wsman", "enumerate", "%s/%s" % (SCHEMA, class_name),
            "-N", namespace, "-u", self.user, "-p", self.password,
            "-h", self.host, "-P", 443, "-v", "-j", "urf-8",
            "-y", "basic", "-o" "-m", 256, "-V", "-c", self._get_cert(),
        ]
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
    pass


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

