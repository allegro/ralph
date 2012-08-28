#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.cmdb.integration.jira import Jira

class NullBugtracker(object):
    def create_issue(self, *args, **kwargs):
        return None

    def find_issuse(self, *args, **kwargs):
        return None

    def user_exists(self, *args, **kwargs):
        return None


class Bugtracker(object):
    """ Very simple fascade for bugtracker systems """
    def __init__(self):
        if settings.BUGTRACKER == 'JIRA':
            self.concrete = Jira()
        else:
            self.concrete = NullBugtracker

    def create_issue(self, *args, **kwargs):
        return self.concrete.create_issue(args, kwargs)

    def find_issuse(self, *args, **kwargs):
        return self.concrete.find_issue(args, kwargs)

    def user_exists(self, *args, **kwargs):
        return self.concrete.user_exists(args, kwargs)


