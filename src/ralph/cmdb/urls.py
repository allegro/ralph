#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns
from django.contrib.auth.decorators import login_required

from ralph.cmdb.views import (Index, Search, Edit, Add, View,
        ViewIframe, EditRelation, LastChanges, AddRelation,
        ViewJira, ViewUnknown)
from ralph.cmdb.views_changes import  (Changes, Problems, Incidents,
        Change, Dashboard, Reports, DashboardDetails)
from ralph.cmdb.views_changes import TimeLine
from django.conf.urls.defaults import include


urlpatterns = patterns('',
    (r'^$', login_required(Index.as_view())),
    (r'^search$', login_required(Search.as_view())),
    (r'^ci/view/(?P<ci_id>\w+)$', login_required(View.as_view())),
    (r'^ci/view/(?P<ci_id>[a-z]{2}-[0-9]+)$', login_required(View.as_view())),
    (r'^ci/view_iframe/(?P<ci_id>\w+)$', login_required(ViewIframe.as_view())),
    (r'^ci/view_jira/(?P<ci_uid>.*)$', login_required(ViewJira.as_view())),
    (r'^ci/jira_ci_unknown/$', login_required(ViewUnknown.as_view())),
    (r'^ci/edit/(?P<ci_id>\w+)$', login_required(Edit.as_view())),
    (r'^ci/get_last_changes/(?P<ci_id>.*)$', login_required(LastChanges.as_view())),
    (r'^relation/add/(?P<ci_id>\w+)$', login_required(AddRelation.as_view())),
    (r'^relation/delete/(?P<relation_id>\w+)/(?P<ci_id>\w+)$', login_required(EditRelation.as_view())),
    (r'^relation/edit/(?P<relation_id>\w+)$', login_required(EditRelation.as_view())),
    (r'^add/$', login_required(Add.as_view())),
    (r'^rest/', include('ralph.cmdb.rest.urls')),
    (r'^changes/change/(?P<change_id>\w+)$', login_required(Change.as_view())),
    (r'^changes/changes$', login_required(Changes.as_view())),
    (r'^changes/incidents$', login_required(Incidents.as_view())),
    (r'^changes/problems$', login_required(Problems.as_view())),

    (r'^changes/timeline$', login_required(TimeLine.as_view())),
    (r'^changes/timeline_ajax$', login_required(TimeLine.get_ajax)),

    (r'^changes/dashboard$', login_required(Dashboard.as_view())),
    (r'^changes/dashboard_ajax$', login_required(Dashboard.get_ajax)),
    (r'^changes/dashboard_details/(?P<type>[0-9]+)/(?P<prio>[0-9]+)/'
    '(?P<month>[0-9]+)/(?P<report_type>\w+)$', \
            login_required(DashboardDetails.as_view())),
    (r'^changes/reports$', login_required(Reports.as_view())),
)
