#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
from django.test import TestCase
from ralph.cmdb.integration.issuetracker_plugins.jira import JiraRSS
from ralph.deployment.models import DeploymentPoll

CURRENT_DIR = settings.CURRENT_DIR

class JiraRssTest(TestCase):
    def test_get_new_issues(self):
        dp1_1 = DeploymentPoll(key='RALPH-341',
                               date=datetime.strptime('1-1-2012 1:10',
                                                      '%d-%m-%Y %H:%M'))
        dp1_1.save()
        dp1_2 = DeploymentPoll(key='RALPH-341',
                               date=datetime.strptime('1-1-2012 1:20',
                                                      '%d-%m-%Y %H:%M'))
        dp1_2.save()

        dp2_1 = DeploymentPoll(key='RALPH-342',
                               date=datetime.strptime('2-2-2012 2:10',
                                                      '%d-%m-%Y %H:%M'),
                               checked=False)
        dp2_1.save()
        dp2_2 = DeploymentPoll(key='RALPH-342',
                               date=datetime.strptime('2-2-2012 2:20',
                                                      '%d-%m-%Y %H:%M'),
                               checked=False)
        dp2_2.save()

        dp3_1 = DeploymentPoll(key='RALPH-343',
                               date=datetime.strptime('3-3-2012 3:10',
                                                      '%d-%m-%Y %H:%M'))
        dp3_1.save()
        dp3_2 = DeploymentPoll(key='RALPH-343',
                               date=datetime.strptime('3-3-2012 3:20',
                                                      '%d-%m-%Y %H:%M'))
        dp3_2.save()

        dp4_1 = DeploymentPoll(key='RALPH-344',
                               date=datetime.strptime('4-4-2012 5:10',
                                                      '%d-%m-%Y %H:%M'))
        dp4_1.save()

        x = JiraRSS()
        rss = open(CURRENT_DIR + 'cmdb/tests/samples/jira_rss.xml').read()
        x.rss_url = rss

        self.assertEquals(sorted(x.get_new_issues()),
            ['RALPH-341', 'RALPH-342', 'RALPH-343', 'RALPH-344'])