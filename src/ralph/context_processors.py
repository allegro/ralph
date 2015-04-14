# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph import VERSION


def info(request):
    return {
        'VERSION': '.'.join(VERSION),
        'BUGTRACKER_URL': settings.BUGTRACKER_URL,
        'CHANGELOG_URL': settings.CHANGELOG_URL,
        'TRACKING_CODE': settings.TRACKING_CODE,
    }
