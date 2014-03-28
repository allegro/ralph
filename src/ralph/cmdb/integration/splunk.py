#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import socket

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse

SPLUNK_PORT = settings.SPLUNK_LOGGER_PORT
SPLUNK_HOST = settings.SPLUNK_LOGGER_HOST


class SplunkLogger(object):

    def __init__(self):
        if not SPLUNK_HOST:
            raise ImproperlyConfigured(
                'settings.SPLUNK_HOST is not configured'
            )

    def log(self, message):
        if message:
            self._send_log_record(message)

    def log_dict(self, message):
        if message:
            message = self._prepare_record(message)
            self._send_log_record(message)

    def _send_log_record(self, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SPLUNK_HOST, SPLUNK_PORT))
        s.send(message)
        s.close()

    def _prepare_record(self, message):
        return ' '.join(
            ['|#{}={}#|'.format(
                repr(key), repr(value)
            ) for (key, value) in message.items() if not key.startswith('_')]
        )


def log_change_to_splunk(instance, log_type):
    message = vars(instance)
    message['type'] = log_type
    if hasattr(instance, 'ci'):
        message['ci_name'] = instance.ci.name if instance.ci else None
        message['ralph_link'] = reverse(
            'ci_view_main', kwargs={'ci_id': instance.ci.id}
        ) if instance.ci else None
    if getattr(instance, 'user', None):
        message['author'] = instance.user.username
    if getattr(instance, 'device', None):
        message['device_name'] = instance.device.name
        message['venture'] = instance.device.venture.name
        message['role'] = instance.device.venture_role.name
    SplunkLogger().log_dict(message)
