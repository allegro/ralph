#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.cmdb.integration.lib.jira import Jira


class NullBugtracker(object):
    def create_issue(self, *args, **kwargs):
        return dict(key='#123456')

    def find_issuse(self, *args, **kwargs):
        return [{}]

    def user_exists(self, *args, **kwargs):
        # paranoia answer every time.
        return True


class Bugtracker(object):
    """ Very simple fascade for bugtracker systems """
    def __init__(self):
        if settings.BUGTRACKER == 'JIRA':
            self.concrete = Jira()
        elif settings.BUGTRACKER == 'FAKE':
            self.concrete = NullBugtracker

    def __getattr__(self, name):
        return getattr(self.concrete, name )

