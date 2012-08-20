#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.dispatch import receiver
from django.db.models.signals import post_save

from ralph.cmdb import models  as cdb
import datetime


@receiver(post_save, sender=cdb.CIChangeCMDBHistory, dispatch_uid='ralph.cmdb.cichangecmdbhistory')
def change_post_save(sender, instance, raw, using, **kwargs):
    """ Classify change, and create record - CIChange """
    # now decide if this is a change included into the statistics
    # if yest, create CIChange. Not sure now, so take all data.
    ch = cdb.CIChange()
    ch.time = instance.time
    ch.ci = instance.ci
    ch.priority = cdb.CI_CHANGE_PRIORITY_TYPES.NOTICE.id
    ch.type = cdb.CI_CHANGE_TYPES.CI.id
    ch.content_object = instance
    ch.message = instance.comment
    ch.save()


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
        ch = cdb.CIChangeCMDBHistory()
        if getattr(instance, 'parent_id'):
            ci = instance.parent
        else:
            ci = instance
        ch.ci = ci
        ch.time = datetime.datetime.now()
        ch.field_name = field
        ch.old_value = unicode(orig)
        ch.new_value = unicode(getattr(instance, field))
        ch.user = instance.saving_user
        if instance.id:
            ch.comment = 'Record updated.'
        else:
            ch.comment = 'Record created'
        ch.save()

