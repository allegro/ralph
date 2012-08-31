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

from ralph.deployment.models import (DeploymentStatus, 
        DeploymentPooler, deployment_accepted)


class JiraRSS(object):
    def __init__(self):
        issuetracker_url = settings.ISSUETRACKERS['default']['OPA']['RSS_URL']
        project = settings.ISSUETRACKERS['default']['OPA']['CMDB_PROJECT']
        user = settings.ISSUETRACKERS['default']['OPA']['USER']
        password = settings.ISSUETRACKERS['default']['OPA']['PASSWORD']
        rss_url ='http://%s%s%s/activity?streams=key+IS+%s&os_authType=basic' % \
                (user, password, issuetracker_url[7:], project)
                
    def update_issues(self, issues):
        for item in issues:
            key = item
            date = issues[item]
            new_issue = DeploymentPooler(key=key, date=date)
            try:
                db_issue = DeploymentPooler.get(key=key, date__gte=date, checked=False)
                if db_issue.date <= new_issue.date:
                    new_issue.save()
            except DeploymentPooler.DoesNotExist:
                new_issue.save()

    def get_issues(self):
        issues = DeploymentPooler.filter(checked=False)
        new_issues = []
        for issue in issues:
            new_issues.append(issue)
        return new_issues

    def parse_rss(self, rss_url):
        feed = feedparser.parse(rss_url)
        issues = {}
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


class IntegrityError(Exception):
    pass


class JiraAcceptance(object):

    def accept_deployment(self, deployment):
        deployment_accepted.send(sender=deployment, deployment_id=deployment.id)

    def __init__(self):
        self.acceptance_status = 'accept'
        self.tracker = IssueTracker()
        # can move to IN_PROGRESS = Accepted
        self.accepted_transition = settings.ISSUETRACKERS['default']['OPA']['ACTIONS']['IN_PROGRESS']

    def deployment_accepted(self, deployment):
        if deployment.status != DeploymentStatus.open.id:
            raise IntegrityError("Expected status open, but got %r" % deployment.status)
        issue_transitions = self.tracker.get_issue_transitions(deployment.issue_key).get('transitions')
        issue_transitions_ids = [int(x.get('id')) for x in issue_transitions]
        return self.accepted_transition  in issue_transitions_ids

    def run(self):
        # Unimplemented
        pass

