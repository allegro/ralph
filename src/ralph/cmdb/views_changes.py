#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.utils import simplejson
from django.db.models import Count

import calendar
import datetime

import ralph.cmdb.models  as db
from ralph.cmdb.views import BaseCMDBView, get_icon_for
from ralph.cmdb.forms import CIChangeSearchForm, CIReportsParamsForm
from ralph.cmdb.util import PaginatedView

class ChangesBase(BaseCMDBView):
    def get_context_data(self, **kwargs):
        ret = super(ChangesBase, self).get_context_data(**kwargs)
        ret.update({
            'ZABBIX_URL': settings.ZABBIX_URL,
            'SO_URL': settings.SO_URL,
        })
        return ret

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
            self.puppet_reports.append(dict(report=report, logs=puppet_logs))
        elif change.type == db.CI_CHANGE_TYPES.CONF_GIT.id:
            self.git_changes = [dict(
                id=report.id,
                file_paths=', '.join(report.file_paths.split('#')),
                comment=report.comment,
                author=report.author,
                changeset=report.changeset,
            )]
        elif change.type == db.CI_CHANGE_TYPES.DEVICE.id:
            self.device_attributes_changes  = [ report ]
        return super(Change, self).get(*args, **kwargs)


class Changes(ChangesBase, PaginatedView):
    template_name = 'cmdb/search_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(Changes, self).get_context_data(**kwargs)
        ret.update({
            'changes': [ (x,get_icon_for(x.ci)) for x in self.changes ],
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
        self.paginate(changes)
        self.changes = self.page_contents
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt,type,priority,MONTH(ch.time) as date
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            WHERE YEAR(ch.time)=YEAR(NOW())
            GROUP BY type, priority, MONTH(ch.time)
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


class Problems(ChangesBase, PaginatedView):
    template_name = 'cmdb/search_problems.html'

    def get_context_data(self, **kwargs):
        ret = super(Problems, self).get_context_data(**kwargs)
        ret.update({
            'problems': self.data,
            'jira_url': settings.JIRA_URL + '/browse/'
        })
        return ret

    def get(self, *args, **kwargs):
        queryset = db.CIProblem.objects.order_by('-time').all()
        queryset = self.paginate_query(queryset)
        self.data = queryset
        return super(Problems, self).get(*args, **kwargs)


class Incidents(ChangesBase, PaginatedView):
    template_name = 'cmdb/search_incidents.html'

    def get_context_data(self, **kwargs):
        ret = super(Incidents, self).get_context_data(**kwargs)
        ret.update({
            'incidents' : self.data,
            'jira_url': settings.JIRA_URL + '/browse/',
        })
        return ret

    def get(self, *args, **kwargs):
        queryset = db.CIIncident.objects.order_by('-time').all()
        queryset = self.paginate_query(queryset)
        self.data = queryset
        return super(Incidents, self).get(*args, **kwargs)

class DashboardDetails(ChangesBase, PaginatedView):
    template_name = 'cmdb/dashboard_details_ci.html'

    def get_context_data(self, **kwargs):
        ret = super(DashboardDetails, self).get_context_data(**kwargs)
        ret.update({
            'statistics' : self.data,
        })
        return ret

    def get_csv_data(self):
        report_type = self.kwargs.get('report_type')
        if report_type == 'ci':
            self.csv_data = [(unicode(x['name']),
                unicode(x['count']),
                unicode(x['venture'])) for x in self.data ]
        else:
            self.csv_data = [ (unicode(x[0]), unicode(x[1])) for x in self.data ]
        return self.csv_data

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
            ORDER BY COUNT(*) DESC, cc.name ASC
        ''', [ type, prio, month] )
        if report_type == 'ci':
            self.data = []
            rows = cursor.fetchall()
            for r in rows:
                venture=None
                count = r[0]
                name = r[1]
                ci_id = r[2]
                if ci_id:
                    ci = db.CI.objects.get(id=ci_id)
                    if ci and ci_id and ci.content_object and \
                            getattr(ci.content_object, 'venture', None):
                        venture=db.CI.get_by_content_object(ci.content_object.venture)
                if venture_id:
                    if venture and venture.name == venture_id:
                        self.data.append(dict(
                            count=count,
                            name=name,
                            ci_id=ci_id,
                            venture=venture,
                            prio=prio,
                            type=type))
                else:
                    self.data.append(dict(
                        count=count,
                        name=name,
                        ci_id=ci_id,
                        venture=venture,
                        prio=prio,
                        type=type,
                    ))
            self.paginate(self.data)
            self.data = self.page_contents
        else:
            self.template_name = 'cmdb/dashboard_details_venture.html'
            self.data_dict = {}
            rows = cursor.fetchall()
            for r in rows:
                venture=None
                count = r[0]
                name = r[1]
                ci_id = r[2]
                if ci_id:
                    ci = db.CI.objects.get(id=ci_id)
                    if ci and ci_id and ci.content_object and \
                            getattr(ci.content_object, 'venture',None) :
                        venture=db.CI.get_by_content_object(ci.content_object.venture)
                if not self.data_dict.get(venture, None):
                    self.data_dict[venture] = count
                else:
                    self.data_dict[venture] +=count
            self.data = [ (self.data_dict[x], x) for x in self.data_dict]
            self.data = sorted(self.data, reverse=True)
            self.paginate(self.data)
            self.data = self.page_contents
        return super(DashboardDetails, self).get(*args)


class Dashboard(ChangesBase):
    template_name = 'cmdb/dashboard_main.html'

    def get_context_data(self, **kwargs):
        ret = super(Dashboard, self).get_context_data(**kwargs)
        ret.update({
            'statistics' : self.data,
        })
        return ret

    @classmethod
    def get_ajax(cls, *args):
        data={}
        data_gen = cls.get_generic_data()
        for r in data_gen:
            month = r[3]
            count = r[0]
            type_id = r[1]
            priority_id = r[2]
            month_name =calendar.month_name[month]
            if not (data.get("%d_%d" % (type_id, priority_id))):
                data["%d_%d" % (type_id, priority_id)] = {}

            data["%d_%d" % (type_id, priority_id)][month] = dict(
                    month_name=month_name,
                    count=count,
                    priority=r[2],
                    type=r[1],
            )
        response_dict={'data' : data}
        return HttpResponse(
                simplejson.dumps(response_dict),
                mimetype='application/json',
        )

    def get(self, *args, **kwargs):
        self.data = self.calculate_dashboard()
        return super(Dashboard, self).get(*args)

    @classmethod
    def get_generic_data(cls):
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
        rows = cursor.fetchall()
        return rows

    @classmethod
    def calculate_dashboard(cls):
        data = dict()
        rows = cls.get_generic_data()
        for r in rows:
            month = r[3]
            month_name = calendar.month_name[r[3]]
            count = r[0]
            type = dict(db.CI_CHANGE_TYPES())[r[1]]
            priority = dict(db.CI_CHANGE_PRIORITY_TYPES())[r[2]]
            if not data.get(type):
                data[type] = {}
            if not data.get(type).get(priority):
                data[type][priority] = {}
            data[type][priority][month] = dict(
                    month_name=month_name,
                    count=count,
                    priority=r[2],
                    type=r[1],
            )
        return data

class Reports(ChangesBase, PaginatedView):
    template_name = 'cmdb/view_report.html'
    exporting_csv_file = False

    def get_context_data(self, **kwargs):
        ret = super(Reports, self).get_context_data(**kwargs)
        ret.update({
            'data' : self.data,
            'form' : self.form,
            'report_kind' : self.request.GET.get('kind', 'top'),
            'report_name' : self.report_name,
        })
        return ret

    def first_day_of_month(self, dt):
        ddays = int(dt.strftime("%d"))-1
        delta = datetime.timedelta(days= ddays)
        return dt - delta

    def handle_params(self, queryset):
        beginning = self.first_day_of_month(datetime.date.today())
        beginning = beginning.strftime("%Y-%m-%d")
        if self.request.GET.get('this_month'):
            queryset = queryset.filter(cichange__time__gt=beginning)
        return queryset

    def top_ci_problems(self):
        queryset = db.CI.objects.annotate(num=Count('ciproblem')).order_by('-num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [ (x.num, x) for x in queryset]
        return rows

    def top_ci_incidents(self):
        queryset = db.CI.objects.annotate(num=Count('ciincident')).order_by('-num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [ (x.num, x) for x in queryset]
        return rows

    def least_ci_changes(self):
        queryset = db.CI.objects.annotate(num=Count('cichange')).\
                filter(num=0).order_by('num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [ (x.num, x) for x in queryset]
        return rows

    def top_ci_changes(self):
        queryset = db.CI.objects.annotate(num=Count('cichange')).order_by('-num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [ (x.num, x) for x in queryset]
        return rows

    def get_csv_data(self):
        self.csv_data = [ (unicode(x[0]), unicode(x[1])) for x in self.data ]
        return self.csv_data

    def handle_csv_export(self):
        self.exporting_csv_file = True
        # go on now, but remember to disable pagination while exporting.

    def populate_data(self, *args, **kwargs):
        report_type = self.request.GET.get('kind', 'top')
        if report_type == 'top_changes':
            self.data = self.top_ci_changes()
            self.report_name = 'Top CI Changes'
        elif report_type == 'top_problems':
            self.data = self.top_ci_problems()
            self.report_name = 'Top CI Problems'
        elif report_type == 'top_incidents':
            self.data = self.top_ci_incidents()
            self.report_name = 'Top CI Incidents'
        elif report_type == 'usage':
            self.report_name = 'Top CI Incidents'
            self.data = self.least_ci_changes()
        else:
            raise UserWarning("Unknown report type %s " % report_type)

    def get(self, *args, **kwargs):
        values = self.request.GET
        self.form = CIReportsParamsForm(initial=values)
        changes  = db.CIChange.objects.filter()
        if values.get('type'):
            changes = changes.filter(type__icontains=values.get('type'))
        if values.get('priority'):
            changes = changes.filter(priority__icontains=values.get('priority'))
        if values.get('uid'):
            changes = changes.filter(ci__name=values.get('uid'))
        changes = changes.order_by('-time').all()
        self.populate_data()
        if self.request.GET.get('export') == 'csv':
            # return different http response
            return self.do_csv_export()

        return super(Reports, self).get(*args)

