#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.util import plugin
from ralph.deployment.models import Deployment


@plugin.register(chain='deployment', requires=['ticket'], priority=0)
def puppet(deployment_id):
    if not settings.PUPPET_DB_URL:
        return True
    deployment = Deployment.objects.get(id=deployment_id)
    return deployment.puppet_certificate_revoked
