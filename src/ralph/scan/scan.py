# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


SLOWSCAN_PLUGINS = {}


def scan_address(address, plugins=()):
    for plugin_name in plugins:
        plugin_func = SLOWSCAN_PLUGINS[plugin_name]
        yield plugin_func(address)

