#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.decorators import login_required

from ralph.cmdb.views import (
    Add,
    AddRelation,
    CIChangesEdit,
    CIChangesView,
    CIGitEdit,
    CIGitView,
    CIIncidentsEdit,
    CIIncidentsView,
    CIProblemsEdit,
    CIProblemsView,
    JiraChangesView,
    CIPuppetEdit,
    CIPuppetView,
    CIRalphEdit,
    CIRalphView,
    CIRelationsEdit,
    CIRelationsView,
    CIZabbixEdit,
    CIZabbixView,
    EditRelation,
    Index,
    LastChanges,
    MainCIEdit,
    MainCIView,
    Search,
    ViewUnknown,
    Cleanup,
)
from ralph.cmdb.views_changes import (
    Change,
    Changes,
    Dashboard,
    DashboardDetails,
    Incidents,
    Problems,
    JiraChanges,
    Reports,
    TimeLine,
)
from ralph.cmdb.views_archive import (
    ArchivedAssetsChanges,
    ArchivedZabbixTriggers,
    ArchivedGitChanges,
    ArchivedPuppetChanges,
    ArchivedCIAttributesChanges,
)
from ralph.cmdb.views import Graphs


urlpatterns = patterns(
    '', (r'^$', login_required(Index.as_view())),
    (r'^search$', login_required(Search.as_view())),

    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)$',
        login_required(MainCIView.as_view()), name='ci_view'),

    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/main/$',
        login_required(MainCIView.as_view()), name='ci_view_main'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/relations/$',
        login_required(CIRelationsView.as_view()), name='ci_view_relation'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/git/$',
        login_required(CIGitView.as_view()), name='ci_view_git'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/puppet/$',
        login_required(CIPuppetView.as_view()), name='ci_view_puppet'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/ralph/$',
        login_required(CIRalphView.as_view()), name='ci_view_ralph'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/ci_changes/$',
        login_required(CIChangesView.as_view()), name='ci_view_changes'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/zabbix/$',
        login_required(CIZabbixView.as_view()), name='ci_view_zabbix'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/problems/$',
        login_required(CIProblemsView.as_view()), name='ci_view_problems'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/incidents/$',
        login_required(CIIncidentsView.as_view()), name='ci_view_incidents'),
    url(r'^ci/view/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/jira_changes/$',
        login_required(JiraChangesView.as_view()), name='ci_view_jira'),
    url(r'^cleanup/$', login_required(Cleanup.as_view()), name='cleanup_view'),

    (r'^ci/jira_ci_unknown/$', login_required(ViewUnknown.as_view())),

    url(r'^ci/edit/(?P<ci_id>\w+)$',
        login_required(MainCIEdit.as_view()), name='ci_edit'),
    url(r'^ci/edit/(?P<ci_id>\w+)/main/$',
        login_required(MainCIEdit.as_view()), name='ci_edit_main'),
    url(r'^ci/edit/(?P<ci_id>\w+)/relations/$',
        login_required(CIRelationsEdit.as_view()), name='ci_edit_relations'),
    url(r'^ci/edit/(?P<ci_id>\w+)/git/$',
        login_required(CIGitEdit.as_view()), name='ci_edit_git'),
    url(r'^ci/edit/(?P<ci_id>\w+)/puppet/$',
        login_required(CIPuppetEdit.as_view()), name='ci_edit_puppet'),
    url(r'^ci/edit/(?P<ci_id>\w+)/ralph/$',
        login_required(CIRalphEdit.as_view()), name='ci_edit_ralph'),
    url(r'^ci/edit/(?P<ci_id>\w+)/ci_changes/$',
        login_required(CIChangesEdit.as_view()), name='ci_edit_ci_changes'),
    url(r'^ci/edit/(?P<ci_id>\w+)/zabbix/$',
        login_required(CIZabbixEdit.as_view()), name='ci_edit_zabbix'),
    url(r'^ci/edit/(?P<ci_id>\w+)/problems/$',
        login_required(CIProblemsEdit.as_view()), name='ci_edit_problems'),
    url(r'^ci/edit/(?P<ci_id>\w+)/incidents/$',
        login_required(CIIncidentsEdit.as_view()), name='ci_edit_incidents'),
    url(r'^ci/edit/(?P<ci_id>[a-z]{0,2}-?[0-9]+)/jira_changes/$',
        login_required(JiraChangesView.as_view()), name='ci_edit_jira'),

    (r'^ci/get_last_changes/(?P<ci_id>.*)$',
     login_required(LastChanges.as_view())),
    (r'^relation/add/(?P<ci_id>\w+)$', login_required(AddRelation.as_view())),
    (r'^relation/delete/(?P<relation_id>\w+)/(?P<ci_id>\w+)$',
     login_required(EditRelation.as_view())),
    (r'^relation/edit/(?P<relation_id>\w+)$',
     login_required(EditRelation.as_view())),
    (r'^add/$', login_required(Add.as_view())),
    (r'^rest/', include('ralph.cmdb.rest.urls')),
    (r'^changes/change/(?P<change_id>\w+)$', login_required(Change.as_view())),
    (r'^changes/changes$', login_required(Changes.as_view())),
    (r'^changes/incidents$', login_required(Incidents.as_view())),
    (r'^changes/problems$', login_required(Problems.as_view())),
    (r'^changes/jira_changes$', login_required(JiraChanges.as_view())),

    url(r'^changes/timeline$',
        login_required(TimeLine.as_view()), name='cmdb_timeline'),
    (r'^changes/timeline_ajax$', login_required(TimeLine.get_ajax)),

    (r'^changes/dashboard$', login_required(Dashboard.as_view())),
    (r'^changes/dashboard_ajax$', login_required(Dashboard.get_ajax)),
    (r'^changes/dashboard_details/(?P<type>[0-9]+)/(?P<prio>[0-9]+)/'
     '(?P<month>[0-9]+)/(?P<report_type>\w+)$',
        login_required(DashboardDetails.as_view())),
    (r'^changes/reports$', login_required(Reports.as_view())),
    url(r'^graphs$', login_required(Graphs.as_view()), name='ci_graphs'),

    url(r'^archive/assets/$',
        login_required(ArchivedAssetsChanges.as_view()), name='archive'),
    url(r'^archive/zabbix/$',
        login_required(ArchivedZabbixTriggers.as_view()), name='archive'),
    url(r'^archive/git/$',
        login_required(ArchivedGitChanges.as_view()), name='archive'),
    url(r'^archive/puppet/$',
        login_required(ArchivedPuppetChanges.as_view()), name='archive'),
    url(r'^archive/cmdb/$',
        login_required(ArchivedCIAttributesChanges.as_view()), name='archive'),
)
