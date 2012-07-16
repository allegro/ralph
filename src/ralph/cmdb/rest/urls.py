#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.conf.urls.defaults import patterns
from ralph.cmdb.rest.rest import commit_hook,notify_puppet_agent

urlpatterns = patterns('',
    (r'^commit_hook/', commit_hook),
    (r'^notify_puppet_agent.*', notify_puppet_agent),
)
