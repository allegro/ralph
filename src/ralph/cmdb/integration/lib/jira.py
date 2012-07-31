#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from restkit import Resource, SimplePool, BasicAuth
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

class Jira(object):
    """ Simple JIRA wrapper around RestKit """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Jira, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        user = settings.JIRA_USER
        password = settings.JIRA_PASSWORD
        jira_url = settings.JIRA_URL
        self.pool = SimplePool(keepalive=2)
        self.auth = BasicAuth(user, password)
        self.base_url = "%s/rest/api/latest" % jira_url

    def get_resource(self,resource_name):
        complete_url= "%s/%s" % (self.base_url , resource_name)
        resource = Resource(complete_url, pool_instance=self.pool, filters=[self.auth])
        return resource

    def call_resource(self, resource_name, params):
       resource = self.get_resource(resource_name)
       response = resource.post(payload=json.dumps(params), headers = {'Content-Type' : 'application/json'})
       ret = json.loads(response.body_string())
       return ret

    def find_issue(self, params):
       resource_name = "search"
       return self.call_resource(resource_name, params)


