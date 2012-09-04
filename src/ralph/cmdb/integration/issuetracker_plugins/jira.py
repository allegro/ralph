#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import feedparser

from datetime import datetime
from django.conf import settings
from exceptions import ValueError
from lck.django.common import nested_commit_on_success
from time import mktime

from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.deployment.models import DeploymentPoll, deployment_accepted


class JiraRSS(object):
    def __init__(self, tracker_name='default'):
        if tracker_name is not 'JIRA':
            raise ValueError('given tracker is not JIRA')
        self.issuetracker_url = settings.ISSUETRACKERS[tracker_name]['URL']
        self.project = settings.ISSUETRACKERS[tracker_name]['CMDB_PROJECT']
        self.user = settings.ISSUETRACKERS[tracker_name]['USER']
        self.password = settings.ISSUETRACKERS[tracker_name]['PASSWORD']
        self.rss_url = 'http://%s:%s@%s/activity?streams=key+IS+%s&os_authType=basic' %\
                       (self.user, self.password, self.issuetracker_url[7:],
                        self.project)

    @nested_commit_on_success
    def update_issues(self, issues):
        for item in issues:
            key = item
            date = issues[item]
            issues, create = DeploymentPoll.concurrent_get_or_create(key=key,
                                                     date__gte=date, checked=False,
                                                     defaults={'date': date})

    def get_issues(self):
        new_issues = []
        issues = DeploymentPoll.objects.filter(checked=False)
        for issue in issues:
            new_issues.append(issue.key)
        return new_issues

    def parse_rss(self, rss_url):
        issues = {}
        feed = feedparser.parse(rss_url)
        for item in feed['entries']:
            issue_key = item['link'].split("/")[-1]
            date_time = datetime.fromtimestamp(mktime(item['updated_parsed']))
            if issue_key in issues:
                if issues[issue_key] <= date_time:
                    issues[issue_key] = date_time
            else:
                issues[issue_key] = date_time
        return issues

    def get_new_issues(self):
        issues = self.parse_rss(self.rss_url)
        self.update_issues(issues)
        return self.get_issues()


class JiraAcceptance(object):
    ''' Fallback class - to be removed.
    Use tracker.deployment_accepted for acceptace checking '''

    def __init__(self):
        self.tracker = IssueTracker()

    def accept_deployment(self, deployment):
        deployment_accepted.send(sender=deployment, deployment_id=deployment.id)

    def deployment_accepted(self, deployment):
        return self.tracker.deployment_accepted(deployment)

    def run(self):
        # Unimplemented
        pass


class IntegrityError(Exception):
    pass
