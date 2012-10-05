#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse
from django.utils import simplejson
from django.db.models import Count

import calendar
import datetime

import ralph.cmdb.models  as db
from ralph.cmdb.models_changes import CI_CHANGE_TYPES
from ralph.cmdb.views import BaseCMDBView, get_icon_for
from ralph.cmdb.forms import CIChangeSearchForm, CIReportsParamsForm
from ralph.cmdb.util import PaginatedView
from ralph.util.views import build_url


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
            'puppet_feedback_errors' : self.puppet_feedback_errors,
            'puppet_feedback_changes' : self.puppet_feedback_changes,
            })
        return ret

    def get(self, *args, **kwargs):
        change_id = kwargs.get('change_id')
        change = get_object_or_404(db.CIChange, id=change_id)
        self.change = change
        self.puppet_reports = []
        self.git_changes = []
        self.device_attributes_changes  = []
        self.puppet_feedback_errors = 0
        self.puppet_feedback_changes = 0
        report = change.content_object
        if change.type == db.CI_CHANGE_TYPES.CONF_AGENT.id:
            puppet_logs = db.PuppetLog.objects.filter(cichange=report)
            self.puppet_reports.append(dict(report=report, logs=puppet_logs))
        elif change.type == db.CI_CHANGE_TYPES.CONF_GIT.id:
            self.git_changes = [dict(
                id=report.id,
                file_paths=', '.join(report.file_paths.split('#')),
                comment=report.comment,
                author=report.author,
                changeset=report.changeset,
            )]
            configuration_version=change.content_object.changeset[0:7]
            self.puppet_feedback_changes = db.CIChangePuppet.objects.filter(
                configuration_version=configuration_version,
                status='changed',
            ).count()
            self.puppet_feedback_errors = db.CIChangePuppet.objects.filter(
                configuration_version=configuration_version,
                status='failed',
            ).count()
        elif change.type == db.CI_CHANGE_TYPES.DEVICE.id:
            self.device_attributes_changes  = [report]
        return super(Change, self).get(*args, **kwargs)


class Changes(ChangesBase, PaginatedView):
    template_name = 'cmdb/search_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(Changes, self).get_context_data(**kwargs)
        subsection = ''
        get_type = self.request.GET.get('type')
        if get_type:
            get_type = int(get_type)
            type = CI_CHANGE_TYPES.NameFromID(get_type)
            subsection += '%s - ' % CI_CHANGE_TYPES.DescFromName(type)
        subsection += 'Changes'
        select = {1: 'repo changes',
                  2: 'agent events',
                  3: 'asset attr. changes',
                  4: 'monitoring events',
                  5: 'status office events',
        }
        sidebar_selected = select.get(get_type, 'all events')
        ret.update({
            'changes': [(x, get_icon_for(x.ci)) for x in self.changes],
            'statistics': self.data,
            'form': self.form,
            'subsection': subsection,
            'sidebar_selected': sidebar_selected,
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
            changes = changes.filter(Q(ci__name__icontains=values.get('uid'))
            | Q(ci__id=values.get('uid')))
        changes = changes.order_by('-time')
        self.paginate(changes)
        self.changes = self.page_contents
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt, type, priority, MONTH(ch.time) as date
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
            'jira_url': build_url(settings.ISSUETRACKERS['default']['URL'], 'browse'),
            'subsection': 'Problems',
             'sidebar_selected': 'problems',
        })
        return ret

    def get(self, *args, **kwargs):
        queryset = db.CIProblem.objects.order_by('-time')
        queryset = self.paginate_query(queryset)
        self.data = queryset
        return super(Problems, self).get(*args, **kwargs)


class Incidents(ChangesBase, PaginatedView):
    template_name = 'cmdb/search_incidents.html'

    def get_context_data(self, **kwargs):
        ret = super(Incidents, self).get_context_data(**kwargs)
        ret.update({
            'incidents': self.data,
            'jira_url': build_url(settings.ISSUETRACKERS['default']['URL'], 'browse'),
            'subsection': 'Incidents',
            'sidebar_selected': 'incidents',
        })
        return ret

    def get(self, *args, **kwargs):
        queryset = db.CIIncident.objects.order_by('-time')
        queryset = self.paginate_query(queryset)
        self.data = queryset
        return super(Incidents, self).get(*args, **kwargs)

class DashboardDetails(ChangesBase, PaginatedView):
    template_name = 'cmdb/dashboard_details_ci.html'

    def get_context_data(self, **kwargs):
        ret = super(DashboardDetails, self).get_context_data(**kwargs)
        ret.update({
            'statistics': self.data,
       })
        return ret

    def get_csv_data(self):
        report_type = self.kwargs.get('report_type')
        if report_type == 'ci':
            self.csv_data = [(unicode(x['name']),
                unicode(x['count']),
                unicode(x['venture'])) for x in self.data]
        else:
            self.csv_data = [(unicode(x[0]), unicode(x[1])) for x in self.data]
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
            COUNT(*) as cnt, cc.name as name, cc.id as ci_id
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            WHERE type=%s AND priority=%s AND MONTH(ch.time)=%s
            AND YEAR(ch.time)=YEAR(NOW())
            GROUP BY cc.id DESC
            ORDER BY COUNT(*) DESC, cc.name ASC
        ''', [type, prio, month] )
        if report_type == 'ci':
            self.data = []
            rows = cursor.fetchall()
            for r in rows:
                venture = None
                count = r[0]
                name = r[1]
                ci_id = r[2]
                if ci_id:
                    ci = db.CI.objects.get(id=ci_id)
                    if ci and ci_id and ci.content_object and \
                            getattr(ci.content_object, 'venture', None):
                        venture=db.CI.get_by_content_object(ci.content_object.venture)
                if venture_id:
                    if (venture) and (
                            (venture.id == int(venture_id))
                            or
                            ((venture == None) and (int(venture_id) == -1))
                            ):
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
                            getattr(ci.content_object, 'venture', None):
                        venture = db.CI.get_by_content_object(ci.content_object.venture)
                if venture:
                    if not self.data_dict.get(venture):
                        self.data_dict[venture.id] = dict(count=count,
                                name=venture.name)
                    else:
                        self.data_dict[venture.id]['count'] += count
                else:
                    if not self.data_dict.get(-1):
                        self.data_dict[-1] = dict(count=count,
                                name='Unassigned')
                    else:
                        self.data_dict[-1]['count']+=count


            self.data = [(self.data_dict[x], x) for x in self.data_dict]
            self.data = sorted(self.data, reverse=True)
            self.paginate(self.data)
            self.data = self.page_contents
        return super(DashboardDetails, self).get(*args)

class DashSubReport(object):
    """
    Subreport for given report type. eg. Git Conf --> Critical or Error
    subreports.
    """
    def __init__(self, type, priority):
        self.report_type_int, self.report_type_str = type
        self.priority_int, self.priority_str = priority

    def __repr__(self):
        return 'DashSubReport type= %s priority=%s' % (
                self.report_type_int,
                self.priority_int,
                )

    def get_month_data(self):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) as cnt, type, priority, MONTH(ch.time) as date
            FROM cmdb_ci cc
            INNER JOIN cmdb_cichange ch ON (cc.id = ch.ci_id)
            WHERE YEAR(ch.time) = YEAR(NOW())
            AND type=%s AND priority=%s
            GROUP BY MONTH(ch.time)
            ORDER BY DATE(ch.time) DESC
        ''', [self.report_type_int, self.priority_int])
        rows = cursor.fetchall()
        return rows

    def calculate_report(self):
        self.data = []
        rows = self.get_month_data()
        for r in rows:
            month = r[3]
            month_name = calendar.month_name[r[3]]
            count = r[0]
            self.data.append(dict(
                month=month,
                month_name=month_name,
                count=count))


class DashReport(object):
    """
    Main report e.g. Git Conf/Service reconf. report
    """
    def __init__(self, report_type):
        self.subreports = []
        self.report_type = report_type
        self.report_type_int, self.report_type_str = report_type

    def has_subreports(self):
        """ Return true if has some data """
        for x in self.subreports:
            if x.data:
                return True
        return False

    def __repr__(self):
        return 'DashReport %s with %d subreports' % (self.report_type,
                len(self.subreports)
        )

    def generate_subreports(self):
        for priority in db.CI_CHANGE_PRIORITY_TYPES():
            sr = DashSubReport(self.report_type, priority)
            sr.calculate_report()
            self.subreports.append(sr)

class Dashboard(ChangesBase):
    template_name = 'cmdb/dashboard_main.html'

    def get_context_data(self, **kwargs):
        ret = super(Dashboard, self).get_context_data(**kwargs)
        ret.update({
            'reports': self.reports,
            'db_supported': self.db_supported,
            'breadcrumb': 'test',
            'subsection': 'Dashboard',
            'sidebar_selected': 'dashboard',
        })
        return ret

    @staticmethod
    def get_ajax(*args, **kwargs):
        """Thin wrapper for Ajax subreports data"""
        data={}
        for _type in db.CI_CHANGE_TYPES():
            d = DashReport(_type)
            d.generate_subreports()
            for subreport in d.subreports:
                for month_data in subreport.data:
                    month = month_data.get('month')
                    count = month_data.get('count')
                    type_id = subreport.report_type_int
                    priority_id = subreport.priority_int
                    month_name = calendar.month_name[month]
                    if not (data.get("%d_%d" % (type_id, priority_id))):
                        data["%d_%d" % (type_id, priority_id)] = {}
                    data["%d_%d" % (type_id, priority_id)][month] = dict(
                        month_name=month_name,
                        count=count,
                        priority=priority_id,
                        type=type_id,
                    )
        response_dict={'data': data}
        return HttpResponse(
                simplejson.dumps(response_dict),
                mimetype='application/json',
        )

    def get(self, *args, **kwargs):
        engine = settings.DATABASES['default'].get('ENGINE')
        if engine != 'django.db.backends.mysql':
            self.db_supported = False
            self.reports = []
            return super(Dashboard, self).get(*args)
        else:
            self.db_supported = True
        self.reports = []
        for _type in db.CI_CHANGE_TYPES():
            d = DashReport(_type)
            d.generate_subreports()
            self.reports.append(d)
        return super(Dashboard, self).get(*args)

class Reports(ChangesBase, PaginatedView):
    template_name = 'cmdb/view_report.html'
    exporting_csv_file = False

    def get_context_data(self, **kwargs):
        subsection = ''
        kind = self.request.GET.get('kind')
        if kind:
            subsection += '%s - ' % self.report_name
        subsection += 'Reports'
        select = {'top_changes': 'top ci changes',
                  'top_problems': 'top ci problems',
                  'top_incidents': 'top ci incidents',
                  'usage': 'cis w/o changes',
        }
        ret = super(Reports, self).get_context_data(**kwargs)
        ret.update({
            'data': self.data,
            'form': self.form,
            'report_kind': self.request.GET.get('kind', 'top'),
            'report_name': self.report_name,
            'subsection': subsection,
            'sidebar_selected': select.get(kind, ''),
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
        rows = [(x.num, x) for x in queryset]
        return rows

    def top_ci_incidents(self):
        queryset = db.CI.objects.annotate(num=Count('ciincident')).order_by('-num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [(x.num, x) for x in queryset]
        return rows

    def least_ci_changes(self):
        queryset = db.CI.objects.annotate(num=Count('cichange')).\
                filter(num=0).order_by('num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [(x.num, x) for x in queryset]
        return rows

    def top_ci_changes(self):
        queryset = db.CI.objects.annotate(num=Count('cichange')).order_by('-num')
        queryset = self.handle_params(queryset)
        queryset = self.paginate_query(queryset)
        rows = [(x.num, x) for x in queryset]
        return rows

    def get_csv_data(self):
        self.csv_data = [(unicode(x[0]), unicode(x[1])) for x in self.data]
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
        changes = changes.order_by('-time')
        self.populate_data()
        if self.request.GET.get('export') == 'csv':
            # return different http response
            return self.do_csv_export()

        return super(Reports, self).get(*args)


def make_jira_url(external_key):
    return settings.ISSUETRACKERS['default']['URL'] + '/' + external_key

class TimeLine(BaseCMDBView):
    template_name = 'cmdb/timeline.html'

    def get_context_data(self, **kwargs):
        ret = super(TimeLine, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_selected': 'timeline view',
            'subsection': 'Time Line',
        })
        return ret

    @staticmethod
    def get_ajax(self):
        interval = self.GET.get('interval')
        get_start_date = self.GET.get('start', datetime.datetime.now())
        get_end_date = self.GET.get('end', datetime.datetime.now())
        if interval == '1':
            plot_title = 'Last 6 hours'
            start_date = datetime.datetime.now() - datetime.timedelta(hours=6)
            stop_date = datetime.datetime.now() + datetime.timedelta(hours=1)
        elif interval == '2':
            plot_title = 'Last day'
            start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            stop_date = datetime.datetime.now() + datetime.timedelta(hours=1)
        elif interval == '3':
            plot_title = 'Last week'
            start_date = datetime.datetime.now() - datetime.timedelta(days=7)
            stop_date = datetime.datetime.now() + datetime.timedelta(hours=1)
        elif interval == '4':
            plot_title = 'Last month'
            start_date = datetime.datetime.now() - datetime.timedelta(days=30)
            stop_date = datetime.datetime.now() + datetime.timedelta(hours=1)
        elif get_start_date or get_end_date:
            plot_title = '%s - %s' % (get_start_date, get_end_date)
            start_date = get_start_date
            stop_date = get_end_date

        manual_changes = db.CIChange.objects.filter(
                    time__gte=start_date,
                    time__lte=stop_date,
                    type=db.CI_CHANGE_TYPES.CONF_GIT.id,
        ).order_by('-time')
        agent_changes_warnings = db.CIChange.objects.filter(
                    time__gte=start_date,
                    time__lte=stop_date,
                    type=db.CI_CHANGE_TYPES.CONF_AGENT.id,
                    priority__in=[
                        db.CI_CHANGE_PRIORITY_TYPES.NOTICE.id,
                        db.CI_CHANGE_PRIORITY_TYPES.WARNING.id,
                    ]
        ).order_by('-time')
        agent_changes_errors = db.CIChange.objects.filter(
                    time__gte=start_date,
                    time__lte=stop_date,
                    type=db.CI_CHANGE_TYPES.CONF_AGENT.id,
                    priority__in=[
                        db.CI_CHANGE_PRIORITY_TYPES.ERROR.id,
                        # critical is not used for puppet agents, though not
                        # mentioned.
                    ]
        ).order_by('-time')
        manual = []
        for change in manual_changes:
            #number of ci affected - error/success
            errors_count = db.CIChangePuppet.objects.filter(
                    configuration_version=change.content_object.changeset[0:7],
                    status='failed').aggregate(num_ci=Count('ci'))
            success_count = db.CIChangePuppet.objects.filter(
                    configuration_version=change.content_object.changeset[0:7],
                    status='changed').aggregate(num_ci=Count('ci'))
            manual.append(dict(
                id=change.id,
                time=change.time.isoformat(),
                author=change.content_object.author,
                comment=change.content_object.comment,
                external_key=change.external_key,
                errors_count=errors_count.get('num_ci'),
                success_count=success_count.get('num_ci'),
            ))
        agent_warnings = []
        for change in agent_changes_warnings:
            agent_warnings.append(dict(
                id=change.id,
                time=change.time.isoformat(),
                comment=change.message,
                external_key=make_jira_url(change.external_key),
            ))
        agent_errors=[]
        for change in agent_changes_errors:
            agent_errors.append(dict(
                id=change.id,
                time=change.time.isoformat(),
                comment=change.message,
                external_key=make_jira_url(change.external_key),
            ))
        response_dict=dict(
                manual=manual,
                agent_warnings=agent_warnings,
                agent_errors=agent_errors,
                plot_title=plot_title
        )
        return HttpResponse(
                simplejson.dumps(response_dict),
                mimetype='application/json',
        )