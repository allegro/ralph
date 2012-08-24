#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from restkit import Resource, SimplePool, BasicAuth, ResourceNotFound
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

class JiraException(Exception):
    pass

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

    def get_resource(self, resource_name):
        complete_url= "%s/%s" % (self.base_url , resource_name)
        resource = Resource(complete_url, pool_instance=self.pool, filters=[self.auth])
        return resource

    def call_resource(self, resource_name, params):
       resource = self.get_resource(resource_name)
       response = resource.post(payload=json.dumps(params),
               headers = {'Content-Type' : 'application/json'})
       ret = json.loads(response.body_string())
       return ret

    def find_issue(self, params):
       resource_name = "search"
       return self.call_resource(resource_name, params)

    def user_exists(self, username):
        resource_name = "user?username=%s" % username
        res = self.get_resource(resource_name)
        try:
           res.get(headers={'Content-Type': 'application/json'})
        except ResourceNotFound:
           return False
        return True

    def create_issue(self, summary, description, ci, assignee,
            template, start='', end=''):
        """ Create new issue.

        Jira Rest accepts following fields:
        "project": {
            "id": "10000"
        },
        "summary": "something's wrong",
        "issuetype": {
            "id": "10000"
        },
        "assignee": {
            "name": "homer"
        },
        "reporter": {
            "name": "smithers"
        },
        "priority": {
            "id": "20000"
        },
        "labels": [
            "bugfix",
            "blitz_test"
        ],
        "timetracking": {
            "originalEstimate": "10",
            "remainingEstimate": "5"
        },
        "security": {
            "id": "10000"
        },
        "versions": [
            {
                "id": "10000"
            }
        ],
        "environment": "environment",
        "description": "description",
        "duedate": "2011-03-11",
        "fixVersions": [
            {
                "id": "10001"
            }
        ],
        "components": [
            {
                "id": "10000"
            }
        ],
        "customfield_60000": "jira-developers",
        "customfield_20000": "06/Jul/11 3:25 PM",
        "customfield_80000": {
            "value": "red"
        },
        "customfield_40000": "this is a text field",
        "customfield_30000": [
            "10000",
            "10002"
        ],
        "customfield_70000": [
            "jira-administrators",
            "jira-users"
        ],
        "customfield_50000": "this is a text area. big text.",
        "customfield_10000": "09/Jun/81"
        }"""
        ci_field_name = settings.JIRA_CI_FIELD_NAME
        ci_name_field_name = settings.JIRA_CI_NAME_FIELD_NAME
        op_issue_type = settings.JIRA_OP_ISSUETYPE
        project = settings.JIRA_CMDB_PROJECT
        template_field_name = settings.JIRA_TEMPLATE_FIELD_NAME

        if ci:
            ci_value = ci.uid
            ci_full_description = ci.get_jira_display()
        else:
            ci_value = ''
            ci_full_description = ''

        try:
            call_result = self.call_resource('issue',
                    params={
                        'fields': {
                            'issuetype': { 'name': op_issue_type },
                            'summary': summary,
                            ci_field_name: ci_value,
                            template_field_name: template,
                            ci_name_field_name: ci_full_description,
                            'assignee': {
                                'name': assignee
                            },
                            'description': description,
                            'project': {
                                'key': project
                                }
                            },
                    }
            )
        except Exception as e:
            # enclose exception as jira exception, for furter analysing
            raise JiraException(e)
        return call_result


