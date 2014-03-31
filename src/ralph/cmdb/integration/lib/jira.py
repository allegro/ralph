#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from restkit import Resource, BasicAuth, ResourceNotFound
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

from ralph.cmdb.integration.exceptions import IssueTrackerException


class Jira(object):

    def __init__(self):
        self.accepted_transition = settings.ISSUETRACKERS[
            'default']['OPA']['ACTIONS']['IN_PROGRESS']
        user = settings.ISSUETRACKERS['default']['USER']
        password = settings.ISSUETRACKERS['default']['PASSWORD']
        jira_url = settings.ISSUETRACKERS['default']['URL']
        self.auth = BasicAuth(user, password)
        self.base_url = "%s/rest/api/latest" % jira_url
        self.resource_headers = {'Content-type': 'application/json'}

    def create_resource(self, resource_name):
        complete_url = "%s/%s" % (self.base_url, resource_name)
        resource = Resource(
            complete_url, filters=[self.auth]
        )
        return resource

    def call_resource(self, resource_name, params):
        resource = self.create_resource(resource_name)
        response = resource.post(
            payload=json.dumps(params), headers=self.resource_headers
        )
        if response:
            b = response.body_string()
            if b:
                ret = json.loads(b)
            else:
                ret = None
        else:
            ret = None
        return ret

    def get_resource(self, resource_name):
        resource = self.create_resource(resource_name)
        response = resource.get(headers=self.resource_headers)
        return json.loads(response.body_string())

    def get_issue(self, issue_key):
        resource_name = "issue/" + issue_key
        return self.get_resource(resource_name)

    def find_issues(self, params):
        resource_name = "search"
        return self.call_resource(resource_name, params)

    def user_exists(self, username):
        resource_name = "user?username=%s" % username
        try:
            self.get_resource(resource_name)
        except ResourceNotFound:
            return False
        return True

    def get_issue_transitions(self, issue_key):
        resource_name = 'issue/%s/transitions' % issue_key
        return self.get_resource(resource_name)

    def transition_issue(self, issue_key, transition_id):
        try:
            call_result = self.call_resource(
                'issue/%s/transitions' % issue_key, params={
                    'update': {
                        'comment': [
                            {
                                'add': {
                                    'body': 'test transition',
                                }
                            }]
                    },
                    'fields': {
                        #                            'resolution': {
                        #                                'name' : 'fixed'
                        #                            }
                    },
                    'transition': {
                        'id': transition_id
                    }
                }
            )
        except Exception as e:
            raise IssueTrackerException(e)
        return call_result

    def create_issue(
            self, summary, description, issue_type, ci, assignee,
            start='', end='', business_assignee=None, technical_assignee=None,
            template=None, service=None, profile=None):
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

        """
        Note: CI Field name is custom field added to bugtracker,
        allowing connection with CMDB. CI field ID is required here.
        You can get it from API or directly inspecting Jira form's HTML.
        """

        s = settings.ISSUETRACKERS['default']
        ci_field_name = s['CI_FIELD_NAME']
        ci_name_field_name = s['CI_NAME_FIELD_NAME']
        project = s['CMDB_PROJECT']
        template_field_name = s['TEMPLATE_FIELD_NAME']
        profile_field_name = s['PROFILE_FIELD_NAME']
        bowner_field_name = s['OPA']['BOWNER_FIELD_NAME']
        towner_field_name = s['OPA']['TOWNER_FIELD_NAME']

        if ci:
            ci_value = ci.uid
            ci_full_description = ci.get_jira_display()
        else:
            ci_value = ''
            ci_full_description = ''

        params = {
            'fields': {
                'issuetype': {'name': issue_type},
                'summary': summary,
                ci_field_name: ci_value,
                ci_name_field_name: ci_full_description,
                'assignee': {
                    'name': assignee
                },
                'description': description,
                'project': {
                    'key': project
                },
            },
        }
        if technical_assignee:
            params['fields'][towner_field_name] = {'name': technical_assignee}
        if business_assignee:
            params['fields'][bowner_field_name] = {'name': business_assignee}
        if template:
            params['fields'][template_field_name] = template
        if profile_field_name and profile:
            params['fields'][profile_field_name] = profile
        logger.debug('Calling with params: %s' % unicode(params))
        try:
            call_result = self.call_resource('issue', params)
        except Exception as e:
            # enclose exception as jira exception, for furter analysing
            raise IssueTrackerException(e)
        return call_result

    def deployment_accepted(self, deployment):
        issue_transitions = self.get_issue_transitions(
            deployment.issue_key).get('transitions')
        issue_transitions_ids = [int(x.get('id')) for x in issue_transitions]
        return self.accepted_transition in issue_transitions_ids
