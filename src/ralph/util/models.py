#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Common models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple

from django.contrib.auth.models import User
from django.db import models as db
from django.db.utils import DatabaseError
from django.dispatch import Signal
from tastypie.models import create_api_key

from ralph.settings import SYNC_FIELD_MIXIN_NOTIFICATIONS_WHITELIST

from django.contrib.auth.tests import models as auth_test_models
ChangeTuple = namedtuple('ChangeTuple', ['field', 'old_value', 'new_value'])


def create_api_key_ignore_dberrors(*args, **kwargs):
    try:
        return create_api_key(*args, **kwargs)
    except DatabaseError:
        # no such table yet, first syncdb
        from django.db import transaction
        transaction.rollback_unless_managed()

db.signals.post_save.connect(create_api_key_ignore_dberrors, sender=User)


# workaround for a unit test bug in Django 1.4.x

del auth_test_models.ProfileTestCase.test_site_profile_not_available

# signal used by SyncFieldMixin for sending notifications on changed fields
fields_synced_signal = Signal(providing_args=['changes', 'change_author'])


class SyncFieldMixin(db.Model):
    """
    Mixin responsible for syncing fields between linked objects. In order to
    specify objects and fields that you want to keep in sync, you need to
    implement 'get_synced_objs_and_fields' method which should return a list of
    tuples, where every such tuple should contain an object and a list of
    fields you want to sync, e.g.:

        [(obj1, [field1, field2]), (obj2, [field1, field3])]

    After syncing your objects, this mixin sends 'fields_synced_signal' which
    carries a list of changes that have been made.

    For example, let's say that you're changing fields 'foo' and 'bar'  on some
    device object and you want to propagate them to an asset which is linked to
    it. In order to do that, your Device class should inherit this mixin and
    implement 'get_synced_objs_and_fields' method, which should return
    something like this:

        [(linked_asset_object, ['foo', 'bar'])]

    Remember that 'linked_asset_object' should have 'foo' and 'bar' fields
    already defined - otherwise it won't make sense.
    """
    class Meta:
        abstract = True

    def get_synced_objs_and_fields(self):
        raise NotImplementedError()

    def save(self, mute=False, visited=None, *args, **kwargs):
        from ralph.ui.views.common import SAVE_PRIORITY
        # by default save with the same priority as in 'edit device' forms etc.
        visited = visited or set()
        visited.add(self)
        priority = kwargs.get('priority')
        change_author = kwargs.get('user')
        if priority is None:
            priority = SAVE_PRIORITY
        changes = []
        for obj, fields in self.get_synced_objs_and_fields():
            if obj in visited:
                continue
            for f in fields:
                setattr(obj, f, getattr(self, f))
            obj.save(visited=visited, mute=True, priority=priority)
        # if 'mute' is False *and* if the given field is not present in
        # SYNC_FIELD_MIXIN_NOTIFICATIONS_WHITELIST, *then* notification of
        # change won't be send
        if not mute:
            changes = []
            try:
                old_obj = type(self).objects.get(pk=self.pk)
            except type(self).DoesNotExist:
                old_obj = None
            for field in self._meta.fields:
                if field.name not in SYNC_FIELD_MIXIN_NOTIFICATIONS_WHITELIST:
                    continue
                old_value = getattr(old_obj, field.name) if old_obj else None
                new_value = getattr(self, field.name)
                if old_value != new_value:
                    changes.append(
                        ChangeTuple(field.name, old_value, new_value)
                    )
            fields_synced_signal.send_robust(
                sender=self, changes=changes, change_author=change_author
            )
        return super(SyncFieldMixin, self).save(*args, **kwargs)
