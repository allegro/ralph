#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.dnsedit import reset_dns


@plugin.register('deployment', ['ticket'], 0)
def dns(deployment):
    reset_dns(deployment.hostanme, deployment.ip)
    return True
