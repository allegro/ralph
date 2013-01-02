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
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, pre_delete
from django.db import IntegrityError
from celery.task import task
import django.dispatch

# using models_ci not models, for dependency chain.
from ralph.cmdb import models_ci as cdb
from ralph.cmdb import models_changes as chdb
from ralph.cmdb.integration.issuetracker import IssueTracker
from ralph.cmdb.integration.exceptions import IssueTrackerException
from ralph.cmdb.models_common import getfunc
from ralph.discovery.models import Device, DataCenter, Network
from ralph.business.models import Venture, VentureRole, Service, BusinessLine


logger = logging.Logger(__name__)

user_match = re.compile(r".*\<(.*)@.*\>")
register_issue_signal = django.dispatch.Signal(providing_args=["change_id"])

if settings.ISSUETRACKERS['default']['ENGINE'] == '':
    # Dont register changes at all.
    RALPH_CHANGE_LINK = '%s'
    OP_TEMPLATE = ''
    OP_ISSUE_TYPE = ''
    DEFAULT_ASSIGNEE = ''
    OP_START_DATE = ''
    OP_PROFILE = ''
    OP_TICKETS_ENABLE = False
else:
    RALPH_CHANGE_LINK = \
        settings.ISSUETRACKERS['default']['CMDB_VIEWCHANGE_LINK']
    OP_TEMPLATE = settings.ISSUETRACKERS['default']['OP']['TEMPLATE']
    OP_PROFILE = settings.ISSUETRACKERS['default']['OP']['PROFILE']
    OP_ISSUE_TYPE = settings.ISSUETRACKERS['default']['OP']['ISSUETYPE']
    DEFAULT_ASSIGNEE = \
        settings.ISSUETRACKERS['default']['OP']['DEFAULT_ASSIGNEE']
    OP_START_DATE = settings.ISSUETRACKERS['default']['OP']['START_DATE']
    OP_TICKETS_ENABLE = \
        settings.ISSUETRACKERS['default']['OP']['ENABLE_TICKETS']


def get_login_from_user(long_user_text):
    """ Return email from 'username <email>'

    >>> user_match.match('Unknown User <unknown@allegro.pl>').groups()[0]
    'unknown'

    """
    matches = user_match.match(long_user_text)
    if matches:
        return matches.groups()[0]
    else:
        return ''


@receiver(post_delete, sender=chdb.CIChangeGit,
          dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangeZabbixTrigger,
          dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangeStatusOfficeIncident,
          dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangeCMDBHistory,
          dispatch_uid='ralph.cmdb.cichangedelete')
@receiver(post_delete, sender=chdb.CIChangePuppet,
          dispatch_uid='ralph.cmdb.cichangedelete')
def change_delete_post_save(sender, instance, **kwargs):
    # remove child cichange
    try:
        parent_change = chdb.CIChange.get_by_content_object(instance)
        parent_change.delete()
    except chdb.CIChange.DoesNotExist:
        # in case of some trash
        pass


@receiver(post_save, sender=chdb.CIChangeCMDBHistory,
          dispatch_uid='ralph.cmdb.change_post_save')
@receiver(post_save, sender=chdb.CIChangePuppet,
          dispatch_uid='ralph.cmdb.change_post_save')
@receiver(post_save, sender=chdb.CIChangeGit,
          dispatch_uid='ralph.cmdb.change_post_save')
def post_create_change(sender, instance, raw, using, **kwargs):
    registration_type = chdb.CI_CHANGE_REGISTRATION_TYPES.NOT_REGISTERED.id
    user = None
    try:
        """ Classify change, and create record - CIChange """
        logger.debug('Hooking post save CIChange creation.')
        if isinstance(instance, chdb.CIChangeGit):
            # register every git change (treat as manual)
            registration_type = chdb.CI_CHANGE_REGISTRATION_TYPES.WAITING.id
            priority = chdb.CI_CHANGE_PRIORITY_TYPES.WARNING.id
            change_type = chdb.CI_CHANGE_TYPES.CONF_GIT.id
            message = instance.comment
            if instance.time:
                time = instance.time
            else:
                time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ci = instance.ci
        elif isinstance(instance, chdb.CIChangeCMDBHistory):
            # register only user triggered cmdb history
            if instance.user_id:
                registration_type = \
                    chdb.CI_CHANGE_REGISTRATION_TYPES.WAITING.id
                user = instance.user
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
            message = 'Puppet log for %s (%s)' % (
                instance.host, instance.configuration_version
            )

        if chdb.CIChange.objects.filter(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
        ).exists():
            # already created parent cichange(e.g while saving for 2 time). Skip it.
            return
        ch = chdb.CIChange()
        ch.time = time
        ch.ci = ci
        ch.registration_type = registration_type
        ch.priority = priority
        ch.type = change_type
        ch.content_object = instance
        ch.message = message
        ch.user = user
        ch.save()
        # register ticket now.
        register_issue_signal.send(sender=instance, change_id=ch.id)
        logger.debug('Hook done.')
    except IntegrityError:
        instance.delete()
        raise


def can_register_change(instance):
    if not OP_TEMPLATE or not OP_START_DATE or not OP_TICKETS_ENABLE:
        logger.debug(
            'Settings not configured for OP tickets registration. Skipping.')
        return False
    return (
        (instance.time.date() >= date_from_str(OP_START_DATE))
        and instance.registration_type ==
            chdb.CI_CHANGE_REGISTRATION_TYPES.WAITING.id
            and not instance.external_key
    )


@receiver(
    register_issue_signal, dispatch_uid='register_issue_handler')
def register_issue_handler(sender, change_id, **kwargs):
    instance = chdb.CIChange.objects.get(id=change_id)
    if can_register_change(instance):
        getfunc(create_issue)(instance.id)


@receiver(post_save, sender=cdb.CI, dispatch_uid='ralph.cmdb.history')
@receiver(post_save, sender=cdb.CIRelation, dispatch_uid='ralph.cmdb.history')
def ci_post_save(sender, instance, raw, using, **kwargs):
    """A hook for creating ``CIChangeCMDBHistory`` entries when a CI changes"""
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


@task(queue='cmdb_git')
def create_issue(change_id, retry_count=1):
    ch = chdb.CIChange.objects.get(id=change_id)
    if ch.registration_type == chdb.CI_CHANGE_REGISTRATION_TYPES.OP.id:
        logger.warning('Already registered change id=%d' % change_id)
        return

    user = ''
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
            change_link=RALPH_CHANGE_LINK % (ch.id),
            author=ch.content_object.author,
        ))

    elif ch.type == chdb.CI_CHANGE_TYPES.DEVICE.id:
        user = unicode(ch.content_object.user)
        summary = 'Asset attribute change: %s' % ch.message
        description = '''
        Attribute: %(attribute)s
        Old value: %(old_value)s
        New value: %(new_value)s
        Description: %(description)s
        CMDB link: %(cmdb_link)s
        Author: %(author)s

        ''' % (dict(
            attribute=ch.content_object.field_name,
            old_value=ch.content_object.old_value,
            new_value=ch.content_object.new_value,
            description=ch.content_object.comment,
            author=unicode(ch.content_object.user),
            cmdb_link=RALPH_CHANGE_LINK % (ch.id),
        ))

    elif ch.type == chdb.CI_CHANGE_TYPES.CI.id:
        user = unicode(ch.content_object.user)
        summary = 'CMDB attribute change: %s' % ch.message
        description = '''
        Attribute: %(attribute)s
        Old value: %(old_value)s
        New value: %(new_value)s
        Description: %(description)s
        CMDB link: %(cmdb_link)s
        Author: %(author)s
        ''' % (dict(
            attribute=ch.content_object.field_name,
            old_value=ch.content_object.old_value,
            new_value=ch.content_object.new_value,
            description=ch.content_object.comment,
            author=unicode(ch.content_object.user),
            cmdb_link=RALPH_CHANGE_LINK % (ch.id),
        ))
    try:
        j = IssueTracker()
        if ch.ci:
            ci = ch.ci
        else:
            ci = None
        if not j.user_exists(user):
            user = DEFAULT_ASSIGNEE

        issue = j.create_issue(
            summary=summary,
            description=description,
            issue_type=OP_ISSUE_TYPE,
            ci=ci,
            assignee=user,
            template=OP_TEMPLATE,
            start=ch.created.isoformat(),
            end='',
            profile=OP_PROFILE,
        )
        ch = chdb.CIChange.objects.get(id=ch.id)
        # before save, check one more time
        if ch.registration_type == chdb.CI_CHANGE_REGISTRATION_TYPES.OP.id:
            logger.warning('Already registered change id=%d' % change_id)
            return
        ch.registration_type = chdb.CI_CHANGE_REGISTRATION_TYPES.OP.id
        ch.external_key = issue.get('key')
        ch.save()
    except IssueTrackerException as e:
        logger.warning(
            'Issue tracker exception for change: %d (%s)' % (change_id, e)
        )


def date_from_str(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d').date()


@receiver(post_delete, sender=chdb.CIChange,
          dispatch_uid='ralph.cmdb.cichangebasedelete')
def basechange_delete_post_save(sender, instance, **kwargs):
    # remove parent cichange
    content_object = instance.content_object
    if content_object:
        content_object.delete()


@receiver(pre_delete, sender=Device,
          dispatch_uid='ralph.cmdb.deletedevice')
@receiver(pre_delete, sender=Venture,
          dispatch_uid='ralph.cmdb.deletedevice')
@receiver(pre_delete, sender=VentureRole,
          dispatch_uid='ralph.cmdb.deletedevice')
@receiver(pre_delete, sender=DataCenter,
          dispatch_uid='ralph.cmdb.deletedevice')
@receiver(pre_delete, sender=Network,
          dispatch_uid='ralph.cmdb.deletedevice')
@receiver(pre_delete, sender=Service,
          dispatch_uid='ralph.cmdb.deletedevice')
@receiver(pre_delete, sender=BusinessLine,
          dispatch_uid='ralph.cmdb.deletedevice')
def remove_moved_cis_pre_delete(sender, instance, using, **kwargs):
    ci = cdb.CI.get_by_content_object(instance)
    if ci:
        ci.delete()
