#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from ralph.cmdb.integration.bugtracker import Bugtracker

from ralph.cmdb.models_audits import DeploymentStatus, Deployment, \
        deployment_accepted


class JiraRSS(object):
    def __init__(self):
        settings.BUGTRACKER_CMDB_PROJECT #'AGS'
    
    def update_issues(self, issues):
        for item in issue_keys:
            key = item
            date = issue_keys[item]
            new_issue = DeploymentPooler(key=key, date=date)
            try:        
                db_issue = DeploymentPooler.get(key=key, date__gte=date, checked=False)
                if db_issue.date <= dp.date:
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
        issuetracker_url = settings.ISSUETRACKERS['default']['OPA']['RSS_URL']
        project = settings.ISSUETRACKERS['default']['OPA']['CMDB_PROJECT']
        rss_url ='%s/activity?streams=key+IS+%s&os_authType=basic' % (issuetracker_url, project)
        issues = parse_rss(rss_url)
        update_issues(issues)
        return get_issues() 


class JiraAcceptance(object):

    def accept_deployment(self, deployment):
        deployment_accepted.send(sender=deployment, deployment_id=deployment.id)

    def __init__(self):
        self.acceptance_status = 'accept'

    def run(self):
        x = JiraRSS()
        issues = x.get_new_issues()
        for issue in issues:
            exists = False
            try:
                d = Deployment.objects.get(issue_key=issue, status = DeploymentStatus.opened.id)
            except Deployment.DoesNotExist:
                exists = True
            if exists and d.status == DeploymentStatus.opened.id:
                b = Bugtracker()
                jira_issue = b.find_issue(issue)
                if jira_issue.get('status') == self.acceptance_status:
                    self.accept_deployment(issue)
