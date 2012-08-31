#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import feedparser

from time import mktime
from datetime import datetime

from django.conf import settings
from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.deployment.models import DeploymentPoll, deployment_accepted

class JiraRSS(object):
    def __init__(self):
        self.issuetracker_url = settings.ISSUETRACKERS['default']['URL']
        self.project = settings.ISSUETRACKERS['default']['CMDB_PROJECT']
        self.user = settings.ISSUETRACKERS['default']['USER']
        self.password = settings.ISSUETRACKERS['default']['PASSWORD']
        self.rss_url ='http://%s:%s@%s/activity?streams=key+IS+%s&os_authType=basic' % \
                (self.user, self.password, self.issuetracker_url[7:], self.project)

    def update_issues(self, issues):
        for item in issues:
            key = item
            date = issues[item]
            new_issue = DeploymentPoll(key=key, date=date)
            try:
                db_issue = DeploymentPoll.objects.get(key=key, date__gte=date, checked=False)
                if db_issue.date < new_issue.date:
                    new_issue.save()
            except DeploymentPoll.DoesNotExist:
                new_issue.save()

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
        issues = None
        issues = self.parse_rss(self.rss_url)
        self.update_issues(issues)
        return self.get_issues()


class JiraAcceptance(object):
    ''' Fallback class - to be removed.
    Use tracker.deployment_accepted for acceptace checking '''

    def accept_deployment(self, deployment):
        deployment_accepted.send(sender=deployment, deployment_id=deployment.id)

    def __init__(self):
        self.tracker = IssueTracker()

    def deployment_accepted(self, deployment):
        return self.tracker.deployment_accepted(deployment)

    def run(self):
        # Unimplemented
        pass

class IntegrityError(Exception):
    pass
