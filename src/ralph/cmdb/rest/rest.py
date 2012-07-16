#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.views.decorators.csrf import csrf_exempt
import ralph.cmdb.models as db
from ralph.util.views import jsonify
import os

from ralph.cmdb.integration.puppet import PuppetAgentsImporter
from ralph.cmdb.integration.puppet import PuppetGitImporter

""" Web hooks from Jira lands here. """

def unique_file(file_name):
    counter = 1
    file_name_parts = os.path.splitext(file_name) # returns ('/path/file', '.ext')
    while 1:
        try:
            fd = open(file_name,'w')
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
def notify_zabbix(request):
    from cmdb.integration.zabbix import  get_all_hosts
    hosts = get_all_hosts()
    found = 0
    notfound = 0
    notfound_list = []
    for host in hosts:
        hostname = host.get('name')
        hid = host.get('hostid') + "-"
        objs = db.CI.objects.filter(uid__contains = hostname).all()
        if objs:
            objs = objs[0]
            objs[0].zabbix_id = hid
            objs.save()
            found +=1
        else:
            notfound +=1
            notfound_list.append(hostname)

    print "Found: %s" % found
    print "Not found: %s" % notfound
    print ','.join(notfound_list)

@csrf_exempt
@jsonify
def commit_hook(request):
    PuppetGitImporter()
    return dict(status='ok')

