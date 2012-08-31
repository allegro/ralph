#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Łukasz Langa

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lck.django.common import remote_addr, render

from ralph.deployment.models import Deployment, DeploymentStatus

def preboot_view(request):
    ip = remote_addr(request)
    try:
        deployment = Deployment.objects.get(ip=ip,
            status=DeploymentStatus.in_deployment.id)
        # work in progress
    except Deployment.DoesNotExist:
        pass
    return render(request, 'deployment/localboot.txt', locals())
