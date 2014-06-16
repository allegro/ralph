#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import datetime
from django.conf import settings
from django.utils.encoding import force_unicode

from ralph.util import plugin
from ralph.cmdb.integration.base import BaseImporter
from ralph.cmdb.integration.lib import zabbix
from ralph.cmdb.integration.lib.jira import Jira
from ralph.cmdb.integration.util import strip_timezone
from ralph.cmdb import models as db
from ralph.cmdb.util import register_event

# hook git plugins. Screw flake8. Do not delete
from ralph.cmdb.integration.puppet import PuppetGitImporter  # noqa
from ralph.cmdb.integration.ralph import AssetChangeImporter  # noqa

logger = logging.getLogger(__name__)


class ZabbixImporter(BaseImporter):

    """
    Zabbix importer
    """

    def import_hosts(self):
        """
        Create/update zabbix IDn for all matched CI's
        """
        logger.debug('Zabbix hosts import started.')
        hosts = zabbix.get_all_hosts()
        for h in hosts:
            # base method
            ci = self.get_ci_by_name(h.get('host'))
            if not ci:
                continue
            ci.zabbix_id = h.get('hostid')
            ci.save()
        logger.debug('Finshed')

    @staticmethod
    @plugin.register(chain='cmdb_zabbix')
    def zabbix_hosts(**kwargs):
        ZabbixImporter().import_hosts()
        return True, 'Done', kwargs

    @staticmethod
    @plugin.register(chain='cmdb_zabbix', requires=['zabbix_hosts'])
    def zabbix_triggers(**kwargs):
        ZabbixImporter().import_triggers()
        return True, 'Done', kwargs

    def import_triggers(self):
        ''' Create/update zabbix IDn for all matched CI's '''
        triggers = zabbix.get_all_triggers()
        for h in triggers:
            existing = db.CIChangeZabbixTrigger.objects.filter(
                trigger_id=h.get('triggerid')
            ).all()
            if not existing:
                logger.debug('Integrate %s' % h.get('triggerid'))
                c = db.CIChange()
                c.type = db.CI_CHANGE_TYPES.ZABBIX_TRIGGER.id
                c.priority = db.CI_CHANGE_PRIORITY_TYPES.ERROR.id
                # create zabbix type change as container
                ch = db.CIChangeZabbixTrigger()
            else:
                ch = existing[0]
                c = db.CIChange.objects.get(
                    type=db.CI_CHANGE_TYPES.ZABBIX_TRIGGER.id, object_id=ch.id
                )
            ch.ci = self.get_ci_by_name(h.get('host'))
            ch.trigger_id = h.get('triggerid')
            ch.host = h.get('host')
            ch.host_id = h.get('hostid')
            ch.status = h.get('status')
            ch.priority = h.get('priority')
            ch.description = h.get('description')
            ch.lastchange = datetime.datetime.fromtimestamp(
                float(h.get('lastchange'))
            )
            ch.comments = h.get('comments')
            ch.save()
            c.content_object = ch
            c.ci = ch.ci
            c.time = datetime.datetime.fromtimestamp(
                float(h.get('lastchange'))
            )
            c.message = ch.description
            c.save()


class JiraEventsImporter(BaseImporter):

    """
    Jira integration  - Incidents/Problems importing as CI events.
    """
    @staticmethod
    @plugin.register(chain='cmdb_jira')
    def jira_problems(**kwargs):
        cutoff_date = kwargs.get('cutoff_date')
        JiraEventsImporter().import_problem(cutoff_date=cutoff_date)
        return True, 'Done', kwargs

    @staticmethod
    @plugin.register(chain='cmdb_jira')
    def jira_incidents(**kwargs):
        cutoff_date = kwargs.get('cutoff_date')
        JiraEventsImporter().import_incident(cutoff_date=cutoff_date)
        return True, 'Done', kwargs

    @staticmethod
    @plugin.register(chain='cmdb_jira')
    def jira_changes(**kwargs):
        cutoff_date = kwargs.get('cutoff_date')
        JiraEventsImporter().import_jirachange(cutoff_date=cutoff_date)
        return True, 'Done', kwargs

    def tz_time(self, field):
        return strip_timezone(field) if field else None

    def import_obj(self, issue, classtype):
        logger.debug(issue)

        def get_ci(**kwargs):
            if set(kwargs.values()) == {None}:
                return None
            try:
                return db.CI.objects.get(**kwargs)
            except db.CI.DoesNotExist:
                logger.error(
                    'Issue : %s Can''t find ci: %s' %
                    (issue.get('key'), kwargs)
                )

        if settings.ISSUETRACKERS['default'].get('LEGACY_PLUGIN', True):
            ci_obj = get_ci(uid=issue.get('ci'))
            cis = [ci_obj] if ci_obj else []
        else:
            if issue['cis'] is None:
                cis = []
            else:
                cis = [ci for ci in [
                    get_ci(uid=uid) for uid in issue['cis']
                ] if ci]

        obj = classtype.objects.filter(jira_id=issue.get('key')).all()[:1]
        prob = obj[0] if obj else classtype()
        prob.summary = force_unicode(issue.get('summary'))
        prob.status = force_unicode(issue.get('status'))
        prob.assignee = force_unicode(issue.get('assignee'))
        prob.jira_id = force_unicode(issue.get('key'))
        prob.analysis = force_unicode(issue.get('analysis'))[:1024]
        prob.problems = force_unicode(issue.get('problems'))[:1024]
        prob.priority = issue.get('priority')
        prob.issue_type = force_unicode(issue.get('issue_type'))
        prob.description = force_unicode(issue.get('description'))[:1024]
        prob.update_date = self.tz_time(issue.get('update_date'))
        prob.created_date = self.tz_time(issue.get('created_date'))
        prob.resolvet_date = self.tz_time(issue.get('resolvet_date'))
        prob.planned_start_date = self.tz_time(issue.get('planned_start_date'))
        prob.planned_end_date = self.tz_time(issue.get('planned_end_date'))
        prob.save()
        for ci in cis:
            register_event(ci, prob)

    def import_problem(self, cutoff_date=None):
        type = settings.ISSUETRACKERS['default']['PROBLEMS']['ISSUETYPE']
        issues = self.fetch_all(type, cutoff_date)
        for issue in issues:
            self.import_obj(issue, db.CIProblem)

    def import_incident(self, cutoff_date=None):
        type = settings.ISSUETRACKERS['default']['INCIDENTS']['ISSUETYPE']
        issues = self.fetch_all(type, cutoff_date)
        for issue in issues:
            self.import_obj(issue, db.CIIncident)

    def import_jirachange(self, cutoff_date=None):
        for type in settings.ISSUETRACKERS['default']['CHANGES']['ISSUETYPE']:
            issues = self.fetch_all(type, cutoff_date)
            for issue in issues:
                self.import_obj(issue, db.JiraChanges)

    def fetch_all(self, type, cutoff_date=None):
        ci_fieldname = settings.ISSUETRACKERS['default']['CI_FIELD_NAME']
        analysis = settings.ISSUETRACKERS['default'][
            'IMPACT_ANALYSIS_FIELD_NAME'
        ]
        problems_field = settings.ISSUETRACKERS['default'][
            'PROBLEMS_FIELD_NAME'
        ]
        jql = ('type={}'.format(type))
        if cutoff_date is not None:
            jql += " AND (status CHANGED AFTER '{c}' OR created > '{c}')".\
                format(c=cutoff_date.strftime('%Y/%m/%d %H:%m'))
        params = dict(jql=jql)
        offset = 0
        total = None
        while offset != total:
            params['startAt'] = offset
            issues = Jira().find_issues(params)
            total = issues['total']
            for issue in issues.get('issues'):
                field = issue.get('fields')
                assignee = field.get('assignee')
                problems = field.get(problems_field) or []
                ret_problems = [problem.get('value') for problem in problems]
                selected_problems = (
                    ', '.join(ret_problems)
                    if ret_problems else None
                )
                priority = field.get('priority')
                issuetype = field.get('issuetype')
                result = dict(
                    key=issue.get('key'),
                    description=field.get('description', ''),
                    summary=field.get('summary'),
                    status=field.get('status').get('name'),
                    assignee=assignee.get('displayName') if assignee else '',
                    analysis=field.get(analysis),
                    problems=selected_problems,
                    priority=priority.get('iconUrl') if priority else '',
                    issue_type=issuetype.get('name') if issuetype else '',
                    update_date=field.get('updated'),
                    created_date=field.get('created'),
                    resolvet_date=field.get('resolutiondate'),
                    planned_start_date=field.get('customfield_11602'),
                    planned_end_date=field.get('customfield_11601'),
                )
                # For a legacy plugin we store the sole CI as result['ci']
                # For the new plugin we store all the CIs (both main and
                # additional) as result['cis']
                if settings.ISSUETRACKERS['default'].get(
                    'LEGACY_PLUGIN',
                    True,
                ):
                    result['ci'] = field.get(ci_fieldname)
                    result['cis'] = []
                else:
                    result['ci'] = None
                    result['cis'] = field.get(ci_fieldname)
                yield result
            offset += len(issues['issues'])
            print ("{} of {}".format(offset, total))
