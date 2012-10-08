#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import logging
import re

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from celery.task import task

# using models_ci not models, for dependency chain.
from ralph.cmdb import models_ci as cdb
from ralph.cmdb import models_changes as chdb
from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.cmdb.integration.exceptions import IssueTrackerException
from ralph.cmdb.models_common import getfunc


logger = logging.Logger(__file__)

user_match = re.compile(r".*\<(.*)@.*\>")

if settings.ISSUETRACKERS['default']['ENGINE'] == '':
    # Null Issue Tracker fallback
    ralph_change_link = '%s'
    op_template = ''
    op_issue_type = ''
    default_assignee = ''
else:
    ralph_change_link = settings.ISSUETRACKERS['default']['CMDB_VIEWCHANGE_LINK']
    op_template = settings.ISSUETRACKERS['default']['OP']['TEMPLATE']
    op_issue_type = settings.ISSUETRACKERS['default']['OP']['ISSUETYPE']
    default_assignee = settings.ISSUETRACKERS['default']['OP']['DEFAULT_ASSIGNEE']


def get_login_from_user(long_user_text):
    """ Return email from 'username <email>'

    >>> re.compile(user_match).match('Unknown User <unknown@allegro.pl>').groups()[0]
    'unknown'

    """
    matches = user_match.match(long_user_text)
    if matches:
        return matches.groups()[0]
    else:
        return ''


@receiver(post_save, sender=chdb.CIChangeCMDBHistory, dispatch_uid='ralph.cmdb.change_post_save')
@receiver(post_save, sender=chdb.CIChangePuppet, dispatch_uid='ralph.cmdb.change_post_save')
@receiver(post_save, sender=chdb.CIChangeGit, dispatch_uid='ralph.cmdb.change_post_save')
def post_create_change(sender, instance, raw, using, **kwargs):
    """ Classify change, and create record - CIChange """
    logger.debug('Hooking post save CIChange creation.')
    if isinstance(instance, chdb.CIChangeGit):
        priority = chdb.CI_CHANGE_PRIORITY_TYPES.WARNING.id
        change_type = chdb.CI_CHANGE_TYPES.CONF_GIT.id
        message = instance.comment
        time = instance.time
        ci = instance.ci
    elif isinstance(instance, chdb.CIChangeCMDBHistory):
        change_type = chdb.CI_CHANGE_TYPES.CI.id
        priority = chdb.CI_CHANGE_PRIORITY_TYPES.NOTICE.id
        message = instance.comment
        time = instance.time
        ci = instance.ci
    elif isinstance(instance, chdb.CIChangePuppet):
        if instance.status == 'failed':
            priority = chdb.CI_CHANGE_PRIORITY_TYPES.ERROR.id
        elif instance.status == 'changed':
            priority = chdb.CI_CHANGE_PRIORITY_TYPES.WARNING.id
        else:
            priority = chdb.CI_CHANGE_PRIORITY_TYPES.NOTICE.id
        change_type = chdb.CI_CHANGE_TYPES.CONF_AGENT.id
        time = instance.time
        ci = instance.ci
        message = 'Puppet log for %s (%s)' % (instance.host, instance.configuration_version)

    # now decide if this is a change included into the statistics
    # by default create for every hooked change type.
    ch = chdb.CIChange()
    ch.time = time
    ch.ci = ci
    ch.priority = priority
    ch.type = change_type
    ch.content_object = instance
    ch.message = message
    ch.save()
    logger.debug('Hook done.')

@receiver(post_save, sender=cdb.CI, dispatch_uid='ralph.cmdb.history')
@receiver(post_save, sender=cdb.CIRelation, dispatch_uid='ralph.cmdb.history')
def ci_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``CIChangeCMDBHistory`` entries when a CI changes."""
    for field, orig in instance.dirty_fields.iteritems():
        if field in instance.insignificant_fields:
            continue
        if field.endswith('_id'):
            field = field[:-3]
            orig = instance._meta.get_field_by_name(
                    field
                )[0].related.parent_model.objects.get(
                    pk=orig
                ) if orig is not None else None
        ch = chdb.CIChangeCMDBHistory()
        if getattr(instance, 'parent_id', None):
            ci = instance.parent
        else:
            ci = instance
        ch.ci = ci
        ch.time = datetime.datetime.now()
        ch.field_name = field
        ch.old_value = unicode(orig)
        if field == 'object':
            ch.new_value = 'object'
        else:
            ch.new_value = unicode(getattr(instance, field))
        ch.user = instance.saving_user
        if instance.id:
            ch.comment = 'Record updated.'
        else:
            ch.comment = 'Record created'
        ch.save()

@task
def create_issue(change_id, retry_count=1):
    ch = chdb.CIChange.objects.get(id=change_id)
    if ch.registration_type == chdb.CI_CHANGE_REGISTRATION_TYPES.CHANGE.id:
        raise Exception('Already registered')

    user=''
    if ch.type == chdb.CI_CHANGE_TYPES.CONF_GIT.id:
        user = get_login_from_user(ch.content_object.author)
        summary = 'Config Change: %s' % ch.message
        description = '''
        Changeset id: %(changeset)s
        Source: GIT
        Description: %(summary)s
        CMDB link: %(change_link)s
        Author: %(author)s

        ''' % (dict(
            changeset=ch.content_object.changeset,
            summary=ch.message,
            change_link=ralph_change_link % (ch.id),
            author=ch.content_object.author,
        ))

    elif ch.type == chdb.CI_CHANGE_TYPES.DEVICE.id:
        user = unicode(ch.content_object.user)
        summary = 'Asset attribute change: %s' % ch.message
        description = '''
        Old value: %(old_value)s
        New value: %(new_value)s
        Description: %(description)s
        CMDB link: %(cmdb_link)s
        Author: %(author)s

        ''' % (dict(
            old_value=ch.content_object.old_value,
            new_value=ch.content_object.new_value,
            description=ch.content_object.comment,
            author=unicode(ch.content_object.user),
            cmdb_link=ralph_change_link % (ch.id),
        ))

    elif ch.type == chdb.CI_CHANGE_TYPES.CI.id:
        user = unicode(ch.content_object.user)
        summary = 'CMDB attribute change: %s' % ch.message
        description = '''
        Old value: %(old_value)s
        New value: %(new_value)s
        Description: %(description)s
        CMDB link: %(cmdb_link)s
        Author: %(author)s
        ''' % (dict(
            old_value=ch.content_object.old_value,
            new_value=ch.content_object.new_value,
            description=ch.content_object.comment,
            author=unicode(ch.content_object.user),
            cmdb_link=ralph_change_link % (ch.id),
        ))
    try:
        j = IssueTracker()
        if ch.ci:
            ci = ch.ci
        else:
            ci = None
        if not j.user_exists(user):
            user = default_assignee

        issue = j.create_issue(
                summary=summary,
                description=description,
                issue_type=op_issue_type,
                ci=ci,
                assignee=user,
                template=op_template,
                start=ch.created.isoformat(),
                end='',
        )
        ch.registration_type = chdb.CI_CHANGE_REGISTRATION_TYPES.CHANGE.id
        ch.external_key = issue.get('key')
        ch.save()
    except IssueTrackerException as e:
        raise create_issue.retry(exc=e, args=[change_id,
            retry_count + 1], countdown=60 * (2 ** retry_count),
            max_retries=15) # 22 days

@receiver(post_save, sender=chdb.CIChange, dispatch_uid='ralph.cmdb.cichange')
def change_post_save(sender, instance, raw, using, **kwargs):
    if not op_template:
        logger.debug('Skipping creating ticket since op_template not set in config.')
        return
    if instance.type in chdb.REGISTER_CHANGE_TYPES:
        if not instance.external_key:
            getfunc(create_issue)(instance.id)


@receiver(post_delete, sender=chdb.CIChangeGit, dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangeZabbixTrigger, dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangeStatusOfficeIncident, dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangeCMDBHistory, dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangePuppet, dispatch_uid='ralph.cmdb.cichangedelete')
def change_delete_post_save(sender, instance, **kwargs):
    # remove child cichange
    try:
        parent_change = chdb.CIChange.get_by_content_object(instance)
        parent_change.delete()
    except chdb.CIChange.DoesNotExist as e:
        # in case of some trash
        pass


@receiver(post_delete, sender=chdb.CIChange, dispatch_uid='ralph.cmdb.cichangebasedelete')
def basechange_delete_post_save(sender, instance, **kwargs):
    # remove parent cichange
    content_object = instance.content_object
    if content_object:
        content_object.delete()



