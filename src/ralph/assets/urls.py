#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns
from django.contrib.auth.decorators import login_required

from ralph.assets.views import BackOfficeSearch, DataCenterSearch



urlpatterns = patterns(
#    '', (r'^$', login_required(BackOfficeSearch.as_view())),
    'dc/search', (r'^$', login_required(BackOfficeSearch.as_view())),
    'back_office/search', (r'^$', login_required(DataCenterSearch.as_view())),
)
