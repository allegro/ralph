# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings


NOTIFICATIONS_MAX_ATTEMPTS = getattr(
    settings, 'NOTIFICATIONS_MAX_ATTEMPTS', 10
)
NOTIFICATIONS_QUEUE_NAME = getattr(
    settings, 'NOTIFICATIONS_QUEUE_NAME', 'default'
)
