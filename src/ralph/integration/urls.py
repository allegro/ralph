#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^servertree$', 'ralph.integration.views.servertree'),
    (r'^servertree/(?P<hostname>.+)/$', 'ralph.integration.views.servertree'),
)
