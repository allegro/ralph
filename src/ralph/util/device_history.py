#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Device models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models_device import Device

"""
Run: DJANGO_SETTINGS_MODULE=ralph.settings python util/device_history.py
"""

def get_device_history(id, attr):
    device = Device.objects.get(id=id)
    return device.get_history(attr)

def get_history_value(history_device):
    ret = []
    for value in history_device:
        ret.append({
            'date': value.date,
            'old_value': value.old_value,
            'new_value': value.new_value
        })
    return ret



history = get_device_history(24403, 'name')
devicehistory = get_history_value(history)
