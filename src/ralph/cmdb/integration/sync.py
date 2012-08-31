#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import datetime
from django.conf import settings

from ralph.util import plugin
from ralph.cmdb.integration.base import BaseImporter
from ralph.cmdb.integration.lib import zabbix
from ralph.cmdb.integration.lib.jira import Jira
from ralph.cmdb.integration.util import strip_timezone
from ralph.cmdb import models as db

# hook git plugins
from ralph.cmdb.integration.puppet import PuppetGitImporter
from ralph.cmdb.integration.ralph import AssetChangeImporter
from optparse import OptionParser


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
            ci.zabbix_id=h.get('hostid')
            ci.save()
        logger.debug('Finshed')

    @staticmethod
    @plugin.register(chain='cmdb_zabbix')
    def zabbix_hosts(context):
        x = ZabbixImporter()
        x.import_hosts()
        return (True, 'Done', context)

    @staticmethod
    @plugin.register(chain='cmdb_zabbix', requires=['zabbix_hosts'])
    def zabbix_triggers(context):
        x = ZabbixImporter()
        x.import_triggers()
        return (True, 'Done' ,context)

    def import_triggers(self):
        ''' Create/update zabbix IDn for all matched CI's '''
        triggers = zabbix.get_all_triggers()
        for h in triggers:
            existing = db.CIChangeZabbixTrigger.objects.filter(
                    trigger_id=h.get('triggerid')).all()
            if not existing:
                logger.debug('Integrate %s' % h.get('triggerid'))
                c = db.CIChange()
                c.type = db.CI_CHANGE_TYPES.ZABBIX_TRIGGER.id
                c.priority = db.CI_CHANGE_PRIORITY_TYPES.ERROR.id
                #create zabbix type change as container
                ch = db.CIChangeZabbixTrigger()
            else:
                ch = existing[0]
                c = db.CIChange.objects.get(type=db.CI_CHANGE_TYPES.ZABBIX_TRIGGER.id,object_id=ch.id)
            ch.ci = self.get_ci_by_name(h.get('host'))
            ch.trigger_id = h.get('triggerid')
            ch.host = h.get('host')
            ch.host_id = h.get('hostid')
            ch.status = h.get('status')
            ch.priority = h.get('priority')
            ch.description = h.get('description')
            ch.lastchange = datetime.datetime.fromtimestamp(
                    float(h.get('lastchange')))
            ch.comments = h.get('comments')
            ch.save()
            c.content_object = ch
            c.ci = ch.ci
            c.time = datetime.datetime.fromtimestamp(float(h.get('lastchange')))
            c.message = ch.description
            c.save()

class JiraEventsImporter(BaseImporter):
    """
    Jira integration  - Incidents/Problems importing as CI events.
    """
    @staticmethod
    @plugin.register(chain='cmdb_jira')
    def jira_problems(context):
        x = JiraEventsImporter()
        x.import_problem()
        return (True, 'Done' ,context)

    @staticmethod
    @plugin.register(chain='cmdb_jira')
    def jira_incidents(context):
        x = JiraEventsImporter()
        x.import_incident()
        return (True, 'Done' ,context)

    def import_obj(self, issue, classtype):
        logger.debug(issue)
        try:
            ci_obj=db.CI.objects.get(uid=issue.get('ci'))
        except:
            logger.error('Issue : %s Can''t find ci: %s' % (issue.get('key'),issue.get('ci')))
            ci_obj = None
        obj = classtype.objects.filter(jira_id=issue.get('key')).all()
        if obj:
            prob = obj[0]
        else:
            prob = classtype()
        prob.description = issue.get('description','') or ''
        prob.summary = issue.get('summary')
        prob.status = issue.get('status')
        prob.assignee = issue.get('assignee')
        prob.ci = ci_obj
        prob.time = strip_timezone(issue.get('time')) #created or updated
        prob.jira_id = issue.get('key')
        prob.save()

    def import_problem(self):
        issues = self.fetch_all('Problem')
        for issue in issues:
            self.import_obj(issue,db.CIProblem)

    def import_incident(self):
        issues = self.fetch_all('Incident')
        for issue in issues:
            self.import_obj(issue, db.CIIncident)

    def fetch_all(self, type):
        ci_fieldname = settings.ISSUETRACKERS['default']['CI_FIELD_NAME']
        params = dict(jql='project = AGS and type=%s' % type, maxResults=1024)
        issues = Jira().find_issues(params)
        items_list = []
        for i in issues.get('issues'):
            f = i.get('fields')
            ci_id = f.get(ci_fieldname)
            assignee = f.get('assignee')
            items_list.append(dict(
                ci=ci_id,
                key=i.get('key'),
                description=f.get('description', ''),
                summary=f.get('summary'),
                status=f.get('status').get('name'),
                time=f.get('updated') or f.get('created'),
                assignee=assignee.get('displayName') if assignee else '')
            )
        return items_list

