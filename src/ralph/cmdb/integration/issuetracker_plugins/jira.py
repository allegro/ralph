#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from django.db.models.query import QuerySet

import feedparser

from datetime import datetime
from django.conf import settings
from exceptions import ValueError
from lck.django.common import nested_commit_on_success
from time import mktime

from ralph.deployment.models import DeploymentPoll


class JiraRSS(object):
    def __init__(self, tracker_name='default'):
        if settings.ISSUETRACKERS[tracker_name]['ENGINE'] != 'JIRA':
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
            new_issue = DeploymentPoll(key=key, date=date)
            try:
                DeploymentPoll.objects.get(key=key, date__gte=date, checked=False)
            except DeploymentPoll.DoesNotExist:
                new_issue.save()

    def get_issues(self):
        new_issues = []
        query = DeploymentPoll.objects.filter(checked=False).query
        query.group_by = ['key']
        issues = QuerySet(query=query, model=DeploymentPoll)
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