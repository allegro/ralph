#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.dnsedit.util import reset_dns


@plugin.register(chain='deployment', requires=['ticket'], priority=0)
def dns(deployment):
    reset_dns(deployment.hostname, deployment.ip)
    return True
