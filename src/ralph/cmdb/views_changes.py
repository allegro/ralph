#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from django.shortcuts import get_object_or_404
import ralph.cmdb.models  as db
from ralph.cmdb.views import BaseCMDBView,ROWS_PER_PAGE, _get_pages, get_icon_for
from ralph.cmdb.forms import CIChangeSearchForm
from django.conf import settings
from django.db import connection
import calendar

class ChangesBase(BaseCMDBView):
    pass

class Change(ChangesBase):
    template_name = 'cmdb/view_change.html'

    def get_context_data(self, **kwargs):
        ret = super(Change, self).get_context_data(**kwargs)
        ret.update({
            'change': self.change,
            'puppet_reports': self.puppet_reports,
            'git_changes': self.git_changes,
            'device_attributes_changes': self.device_attributes_changes,
            'fisheye_url': settings.FISHEYE_URL,
            'fisheye_project': settings.FISHEYE_PROJECT_NAME,
            })
        return ret


    def get(self, *args, **kwargs):
        change_id = kwargs.get('change_id')
        change = get_object_or_404(db.CIChange, id=change_id)
        self.change = change
        self.puppet_reports = []
        self.git_changes = []
        self.device_attributes_changes  = []
        report = change.content_object
        if change.type == db.CI_CHANGE_TYPES.CONF_AGENT.id:
            puppet_logs = db.PuppetLog.objects.filter(cichange=report).all()
            self.puppet_reports.append(dict(report=report,logs=puppet_logs))
        elif change.type == db.CI_CHANGE_TYPES.CONF_GIT.id:
            self.git_changes = [report]
        elif change.type == db.CI_CHANGE_TYPES.DEVICE.id:
            self.device_attributes_changes  = [ report ]
        return super(Change, self).get(*args, **kwargs)


class Changes(ChangesBase):
    template_name = 'cmdb/search_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(Changes, self).get_context_data(**kwargs)
        ret.update({
            'changes': [ (x,get_icon_for(x.ci)) for x in self.changes ],
            'page': self.page,
            'pages' : _get_pages(self.paginator, self.page_number),
            'statistics' : self.data,
            'form' : self.form,
        })
        return ret

    def get(self, *args, **kwargs):
        values = self.request.GET
        self.form = CIChangeSearchForm(initial=values)
        changes  = db.CIChange.objects.filter()
        if values.get('type'):
            changes = changes.filter(type__icontains=values.get('type'))
        if values.get('priority'):
            changes = changes.filter(priority__icontains=values.get('priority'))
        if values.get('uid'):
            changes = changes.filter(ci__name=values.get('uid'))
        changes = changes.order_by('-time').all()
        page = self.request.GET.get('page') or 1
        self.page_number = int(page)
        self.paginator = Paginator(changes, ROWS_PER_PAGE)
        try:
            self.page = self.paginator.page(page)
        except PageNotAnInteger:
            self.page = self.paginator.page(1)
            page=1
        except EmptyPage:
            self.page = self.paginator.page(self.paginator.num_pages)
            page = self.paginator.num_pages
        self.changes = self.page
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt,type,priority,MONTH(ch.time) as date
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            WHERE YEAR(ch.time)=YEAR(NOW())
            GROUP BY type,priority,MONTH(ch.time)
            ORDER BY DATE(ch.time) DESC
        ''')
        self.data= dict()
        rows = cursor.fetchall()
        for r in rows:
            month =calendar.month_name[r[3]]
            count = r[0]
            type = dict(db.CI_CHANGE_TYPES())[r[1]]
            priority = dict(db.CI_CHANGE_PRIORITY_TYPES())[r[2]]
            if not self.data.get(type):
                self.data[type] = {}
            if not self.data.get(type).get(priority):
                self.data[type][priority] = {}
            self.data[type][priority][month] = count
        return super(Changes, self).get(*args)


class Problems(ChangesBase):
    template_name = 'cmdb/search_problems.html'

    def get_context_data(self, **kwargs):
        ret = super(Problems, self).get_context_data(**kwargs)
        ret.update({
            'problems': self.problems,
            'jira_url': settings.JIRA_URL + '/browse/'
        })
        return ret

    def get(self, *args, **kwargs):
        self.problems = db.CIProblem.objects.order_by('-time').all()
        return super(Problems, self).get(*args, **kwargs)


class Incidents(ChangesBase):
    template_name = 'cmdb/search_incidents.html'

    def get_context_data(self, **kwargs):
        ret = super(Incidents, self).get_context_data(**kwargs)
        ret.update({
            'incidents': self.incidents,
            'jira_url': settings.JIRA_URL + '/browse/'
        })
        return ret

    def get(self, *args, **kwargs):
        self.incidents = db.CIIncident.objects.order_by('-time').all()
        return super(Incidents, self).get(*args, **kwargs)

class DashboardVenture(ChangesBase):
    template_name = 'cmdb/dashboard_venture_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(DashboardVenture, self).get_context_data(**kwargs)
        ret.update({
            'statistics' : self.data,
        })
        return ret

    def get(self, *args, **kwargs):
        type = kwargs.get('type')
        prio = kwargs.get('prio')
        month = kwargs.get('month')
        report_type = kwargs.get('report_type')
        venture_id = self.request.GET.get('venture_id')
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt, cc.name as name,cc.id as ci_id
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            WHERE type=%s AND priority=%s AND MONTH(ch.time)=%s
            AND YEAR(ch.time)=YEAR(NOW())
            GROUP BY cc.id DESC
            ORDER BY COUNT(*) DESC
        ''', [ type, prio, month] )
        if report_type == 'ci':
            self.data= []
            rows = cursor.fetchall()
            for r in rows:
                venture=None
                count = r[0]
                name = r[1]
                ci_id = r[2]
                if ci_id:
                    ci = db.CI.objects.get(id=ci_id)
                    if ci and ci_id and ci.content_object and getattr(ci.content_object, 'venture',None) :
                        venture=db.CI.get_by_content_object(ci.content_object.venture)
                if venture_id:
                    if venture and venture.name == venture_id:
                        self.data.append([count,name,ci_id,venture,prio,type])
                else:
                    self.data.append([count,name,ci_id,venture,prio,type])
        else:
            self.template_name = 'cmdb/dashboard_venture_changes_ventures.html'
            self.data_dict = {}
            rows = cursor.fetchall()
            for r in rows:
                venture=None
                count = r[0]
                name = r[1]
                ci_id = r[2]
                if ci_id:
                    ci = db.CI.objects.get(id=ci_id)
                    if ci and ci_id and ci.content_object and getattr(ci.content_object, 'venture',None) :
                        venture=db.CI.get_by_content_object(ci.content_object.venture)
                if not self.data_dict.get(venture,None):
                    self.data_dict[venture] = count
                else:
                    self.data_dict[venture] +=count
            self.data = [ (self.data_dict[x],x) for x in self.data_dict]
            self.data = sorted(self.data,reverse=True)

        return super(DashboardVenture, self).get(*args)


class Dashboard(ChangesBase):
    template_name = 'cmdb/dashboard_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(Dashboard, self).get_context_data(**kwargs)
        ret.update({
            'statistics' : self.data,
        })
        return ret

    def get(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt,type,priority,MONTH(ch.time) as date
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            WHERE YEAR(ch.time)=YEAR(NOW())
            GROUP BY type,priority,MONTH(ch.time)
            ORDER BY DATE(ch.time) DESC
        ''')
        self.data= dict()
        rows = cursor.fetchall()
        for r in rows:
            month = r[3]
            month_name = calendar.month_name[r[3]]
            count = r[0]
            type = dict(db.CI_CHANGE_TYPES())[r[1]]
            priority = dict(db.CI_CHANGE_PRIORITY_TYPES())[r[2]]
            if not self.data.get(type):
                self.data[type] = {}
            if not self.data.get(type).get(priority):
                self.data[type][priority] = {}
            self.data[type][priority][month] = [month_name, count, r[2],r[1]]
        return super(Dashboard, self).get(*args)


class Reports(ChangesBase):
    template_name = 'cmdb/view_report.html'

    def get_context_data(self, **kwargs):
        ret = super(Reports, self).get_context_data(**kwargs)
        ret.update({
            'top_ci_changes' : self.top_ci_changes(),
            'top_ci_problems' : self.top_ci_problems(),
            'top_ci_incidents' : self.top_ci_incidents(),
            'least_ci_changes' : self.least_ci_changes(),
            'report_kind' : self.request.GET.get('kind','top'),
        })
        return ret

    def top_ci_problems(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt, cc.id
            FROM cmdb_ciproblem cp
            INNER JOIN cmdb_ci cc ON (cc.id = cp.ci_id)
            GROUP BY cc.id
            ORDER BY COUNT(*) ASC LIMIT 10
        ''')
        rows = [ (x[0], db.CI.objects.filter(id=x[1]).all()[0]) for x in cursor.fetchall()]
        return rows

    def top_ci_incidents(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt, cc.id as id
            FROM cmdb_ciincident ci
            INNER JOIN cmdb_ci cc ON (cc.id = ci.ci_id)
            GROUP BY cc.id
            ORDER BY COUNT(*) ASC LIMIT 10
        ''')
        rows = [ (x[0], db.CI.objects.filter(id=x[1]).all()[0]) for x in cursor.fetchall()]
        return rows

    def least_ci_changes(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT * FROM (SELECT COUNT(ch.id) count,cc.id id
            FROM cmdb_ci cc
            LEFT JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            GROUP BY cc.id) x  WHERE x.count = 0 LIMIT 30
        ''')
        rows = cursor.fetchall()
        rows = [ (x,db.CI.objects.filter(id=x[1]).all()[0]) for x in rows ]
        return rows

    def top_ci_changes(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt, cc.id
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            GROUP BY cc.id
            ORDER BY COUNT(*) DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        rows = [ (x,db.CI.objects.filter(id=x[1]).all()[0]) for x in rows ]
        return rows

    def get(self, *args, **kwargs):
        return super(Reports, self).get(*args)

