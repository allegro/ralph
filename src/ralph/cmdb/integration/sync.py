#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import datetime
from django.conf import settings

from ralph.cmdb.integration.base import BaseImporter
from ralph.cmdb.integration import zabbix
from ralph.cmdb.integration.util import strip_timezone
from ralph.cmdb.integration.ralph import AssetChangeImporter
from ralph.cmdb.integration.puppet import PuppetGitImporter
from ralph.cmdb import models as db


logger = logging.getLogger(__name__)

class ZabbixImporter(BaseImporter):
    def import_hosts(self):
        """
        Create/update zabbix IDn for all matched CI's
        """
        hosts = zabbix.get_all_hosts()
        matched = 0
        not_matched = 0
        list_not_matched = []
        for h in hosts:
            cis = db.CI.objects.filter(name=h.get('host')).all()
            cnt = len(cis)
            if cnt!=1:
                not_matched+=1
                s = 'Host not matched in CMDB: name=%s, id=%s' % (
                        h.get('host'), h.get('hostid'))
                list_not_matched.append(s)
                logger.debug(s)
            else:
                ci = cis[0]
                ci.zabbix_id=h.get('hostid')
                ci.save()
                matched+=1
        logger.debug('Finshed')

    def import_triggers(self):
        ''' Create/update zabbix IDn for all matched CI's '''
        triggers = zabbix.get_all_triggers()
        for h in triggers:
            existing = db.CIChangeZabbixTrigger.objects.filter(
                    trigger_id=h.get('triggerid')).all()
            if existing:
                continue
            logger.debug('Integrate %s' % h.get('triggerid'))
            c = db.CIChange()
            c.type = db.CI_CHANGE_TYPES.ZABBIX_TRIGGER.id
            c.priority = db.CI_CHANGE_PRIORITY_TYPES.ERROR.id
            #create zabbix type change as container
            ch = db.CIChangeZabbixTrigger()
            ch.ci = self.get_ci_by_name(h.get('host'))
            ch.trigger_id = h.get('triggerid')
            ch.host = h.get('host')
            ch.host_id = h.get('hostid')
            ch.status = h.get('status')
            ch.priority = h.get('priority')
            ch.description = h.get('description')
            lastchange = h.get('lastchange')
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
        from ralph.cmdb.integration.jira import Jira
        ci_fieldname = settings.JIRA_CI_CUSTOM_FIELD_NAME
        params = dict(jql='project = AGS and type=%s' % type, maxResults=1024)
        xxx=Jira().find_issue(params)
        items_list = []
        for i in xxx.get('issues'):
            f = i.get('fields')
            ci_id = f.get(ci_fieldname)
            assignee = f.get('assignee')
            items_list.append(dict(
                ci=ci_id,
                key=i.get('key'),
                description=f.get('description',''),
                summary=f.get('summary'),
                status=f.get('status').get('name'),
                time=f.get('updated') or f.get('created'),
                assignee=assignee.get('displayName') if assignee else ''))
        return items_list


def integrate_main():
    from optparse import OptionParser
    usage = "usage: %prog --git --jira --zabbix_hosts --zabbix_triggers --ralph"
    parser = OptionParser(usage)
    parser.add_option('--ralph',
            dest="ralph",
            action="store_true",
            help="Ralph.",
            default=False,
    )
    parser.add_option('--git',
            dest="git",
            action="store_true",
            help="Git.",
            default=False,
    )
    parser.add_option('--jira',
            dest='jira',
            default=False,
            action="store_true",
            help="Jira.",
    )
    parser.add_option('--zabbix_hosts',
            dest='zabbix_hosts',
            action="store_true",
            help="Zabbix.",
            default=False,
    )
    parser.add_option('--zabbix_triggers',
            dest='zabbix_triggers',
            help="Zabbix.",
            action="store_true",
            default=False,
    )
    (options, args) = parser.parse_args()
    import_classes=[]
    """ Fetch all new data from remote services """

    if options.zabbix_hosts:
        import_classes.append([ZabbixImporter, 'import_hosts'])
    elif options.zabbix_triggers:
        import_classes.append([ZabbixImporter, 'import_triggers'])
    elif options.jira:
        import_classes.append([JiraEventsImporter, 'import_problem'])
        import_classes.append([JiraEventsImporter, 'import_incident'])
    elif options.git:
        import_classes.append([PuppetGitImporter, 'import_git'])
    elif options.ralph:
        import_classes.append([AssetChangeImporter, 'import_change'])
    else:
        parser.error("Specify valid option.")
    # Instantiate importers, and gracefully handle error
    for cl in import_classes:
        classname, methodname = cl
        obj = classname()
        method = getattr(obj,  methodname)
        try:
            method()
        except Exception,e:
            obj.handle_integration_error(classname, methodname, e)
            raise
