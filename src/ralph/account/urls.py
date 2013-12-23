#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from ralph.account.views import UserHomePageEdit, BaseUser, ApiKey

urlpatterns = patterns(
    '',
    url(r'^$', login_required(BaseUser.as_view()), name='user_preference'),
    url(
        r'^preferences/home_page$',
        login_required(UserHomePageEdit.as_view()),
        name='user_home_page'
    ),
    url(
        r'^preferences/api_key$',
        login_required(ApiKey.as_view()),
        name='user_api_key'
    ),
)
