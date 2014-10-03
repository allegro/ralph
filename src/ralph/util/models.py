#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Common models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models as db
from django.db.utils import DatabaseError
from django.dispatch import Signal
from tastypie.models import create_api_key


def create_api_key_ignore_dberrors(*args, **kwargs):
    try:
        return create_api_key(*args, **kwargs)
    except DatabaseError:
        # no such table yet, first syncdb
        from django.db import transaction
        transaction.rollback_unless_managed()

db.signals.post_save.connect(create_api_key_ignore_dberrors, sender=User)


# workaround for a unit test bug in Django 1.4.x

from django.contrib.auth.tests import models as auth_test_models
del auth_test_models.ProfileTestCase.test_site_profile_not_available

# signal used by SyncFieldMixin for sending notifications on changed fields
fields_synced_signal = Signal(providing_args=['changes', 'change_author'])


class SyncFieldMixin(object):
    """
    Mixin responsible for syncing fields between linked objects. In order to
    specify objects and fields that you want to keep in sync, you need to
    implement 'get_synced_objs_and_fields' method which should return a list of
    tuples, where every such tuple should contain an object and a list of
    fields you want to sync, e.g.:

        [(obj1, [field1, field2]), (obj2, [field1, field3])]

    After syncing your objects, this mixin sends 'fields_synced_signal' which
    carries a list of changes that have been made.
    """

    def get_synced_objs_and_fields(self):
        raise NotImplementedError()

    def save(self, *args, **kwargs):
        from ralph.ui.views.common import SAVE_PRIORITY
        # by default save with the same priority as in 'edit device' forms etc.
        priority = kwargs.get('priority')
        change_author = kwargs.get('user')
        if priority is None:
            priority = SAVE_PRIORITY
        changes = []
        for obj, fields in self.get_synced_objs_and_fields():
            for f in fields:
                source_old_value = self.dirty_fields.get(f)
                target_old_value = getattr(obj, f)
                new_value = getattr(self, f)
                if new_value not in (source_old_value, target_old_value):
                    changes.append({
                        'field': f,
                        'source': self,
                        'target': obj,
                        'source_old_value': source_old_value,
                        'target_old_value': target_old_value,
                        'new_value': new_value,
                    })
                setattr(obj, f, new_value)
            obj.save(sync_fields=False, priority=priority)
            fields_synced_signal.send_robust(
                sender=self, changes=changes, change_author=change_author
            )
