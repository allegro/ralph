#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ralph.cmdb.integration.lib.jira import Jira


class NullIssueTracker(object):

    def create_issue(self, *args, **kwargs):
        return dict(key='#123456')

    def find_issuses(self, *args, **kwargs):
        return [{}]

    def get_issue(self, issue_key):
        return {}

    def user_exists(self, *args, **kwargs):
        # paranoia answer every time.
        return True

    def deployment_accepted(self, deployment):
        return True

    def transition_issue(self, *args, **kwargs):
        pass


class IntegrityError(Exception):
    pass


class IssueTracker(object):

    """ Very simple fascade for bugtracker systems """

    def __init__(self):
        self.engine = settings.ISSUETRACKERS['default']['ENGINE']
        if self.engine == 'JIRA':
            self.concrete = Jira()
        elif self.engine == '':
            self.concrete = NullIssueTracker()
        else:
            raise ImproperlyConfigured("Engine %s not known" % self.engine)

    def __getattr__(self, name):
        return getattr(self.concrete, name)
