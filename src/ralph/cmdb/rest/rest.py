#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from ralph.account.models import Perm, ralph_permission
from ralph.cmdb.integration.puppet import PuppetAgentsImporter
from ralph.discovery.tasks import run_chain
from ralph.util.views import jsonify

perms = [
    {
        'perm': Perm.has_core_access,
        'msg': _("You don't have permissions for this resource."),
    },
]


@ralph_permission(perms)
@csrf_exempt
@jsonify
def notify_puppet_agent(request):
    contents = request.body
    x = PuppetAgentsImporter()
    x.import_contents(contents)
    return {'ok': True}


@ralph_permission(perms)
@csrf_exempt
@jsonify
def commit_hook(request):
    run_chain({'queue': 'cmdb_git'}, 'cmdb_git')
    return {'status': 'Queued.'}
