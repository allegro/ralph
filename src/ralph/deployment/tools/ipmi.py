#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import subprocess

from django.conf import settings


IPMI_USER = settings.IPMI_USER
IPMI_PASSWORD = settings.IPMI_PASSWORD


class Error(Exception):
    pass


class AuthError(Error):
    pass


class IPMIToolError(Error):
    pass


class IPMI(object):

    def __init__(self, host, user=IPMI_USER, password=IPMI_PASSWORD):
        self.host = host
        self.user = user
        self.password = password

    def tool(self, command, subcommand, param=None):
        command = [
            "ipmitool",
            "-H",
            self.host,
            "-U",
            self.user,
            "-P",
            self.password,
            command,
            subcommand
        ]
        if param:
            command.append(param)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode and err:
            if err.startswith('Invalid user name'):
                raise AuthError('Invalid user name')
            else:
                raise IPMIToolError('Error calling ipmitool: %s' % err)
        return unicode(out, 'utf-8', 'replace')


def ipmi_power_on(host, user=IPMI_USER, password=IPMI_PASSWORD):
    ipmi = IPMI(host, user, password)
    response = ipmi.tool('chassis', 'power', 'on')
    return response.strip().lower().endswith('on')


def ipmi_reboot(host, user=IPMI_USER, password=IPMI_PASSWORD,
                power_on_if_disabled=False):
    ipmi = IPMI(host, user, password)

    response = ipmi.tool('chassis', 'power', 'status')
    if response.strip().lower().endswith('on'):
        response = ipmi.tool('chassis', 'power', 'reset')
        if response.strip().lower().endswith('reset'):
            return True
    elif power_on_if_disabled:
        return ipmi_power_on(host, user, password)
    return False
