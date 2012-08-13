#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from django.views.decorators.csrf import csrf_exempt
from ralph.util.views import jsonify
from ralph.util import plugin

from ralph.cmdb.integration.puppet import PuppetAgentsImporter
from ralph.cmdb.integration.puppet import PuppetGitImporter
from ralph.discovery.tasks import run_chain
import ralph.cmdb.models as db

""" Web hooks from Jira lands here. """


def unique_file(file_name):
    counter = 1
    file_name_parts = os.path.splitext(file_name) # returns ('/path/file', '.ext')
    while 1:
        try:
            fd = open(file_name, 'w')
            return fd
        except :
            pass
        file_name = file_name_parts[0] + '_' + str(counter) + file_name_parts[1]
        counter += 1

@csrf_exempt
@jsonify
def notify_puppet_agent(request):
    contents=request.body
    x = PuppetAgentsImporter()
    x.import_contents(contents)
    return {'ok' : True}

@csrf_exempt
@jsonify
def commit_hook(request):
    context={'context': ''}
    #deferred run
    run = run_chain.delay
    run(context, 'cmdb_git')
    return dict(status='Queued.')

