#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand

from ralph.deployment.models import Deployment, DeploymentStatus
from ralph.deployment.taks import run_deployment


class Command(BaseCommand):
    """Advance all active deployments if possible."""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        for d in Deployment.objects.filter(
            status__in=(
                DeploymentStatus.open.id,
                Deployment.status.in_progress.id,
                Deployment.status.in_deployment.id,
            )):
            run_deployment(d)
