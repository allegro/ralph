#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traceback

from ralph.util import plugin
from ralph.deployment.models import Deployment


def run_deployment(deployment):
    if deployment.is_running:
        return
    deployment.is_running = True
    deployment.save()
    try:
        done = set(
            name.strip() for
            name in
            deployment.done_plugins.split(',')
            if name.strip()
        )
        tried = set(done)
        while True:
            plugins = plugin.next('deployment', done) - tried
            if not plugins:
                break
            name = plugin.highest_priority('deployment', plugins)
            tried.add(name)
            try:
                success = plugin.run(
                    'deployment',
                    name,
                    deployment_id=deployment.id,
                )
            except Exception:
                traceback.print_exc()
            else:
                if success:
                    done.add(name)
        # The plugins might have changed the deployment object.
        deployment = Deployment.objects.get(id=deployment.id)
        deployment.done_plugins = ', '.join(done)
        deployment.save()
    finally:
        deployment.is_running = False
        deployment.save()
