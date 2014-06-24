#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.views.decorators.csrf import csrf_exempt

from ralph.discovery.tasks import run_chain
from ralph.util.views import jsonify


@csrf_exempt
@jsonify
def commit_hook(request):
    run_chain({'queue': 'cmdb_git'}, 'cmdb_git')
    return {'status': 'Queued.'}
