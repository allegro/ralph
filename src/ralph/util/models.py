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
fields_synced_signal = Signal(providing_args=['changes'])


class SyncFieldMixin(object):
    """
    Mixin responsible for syncing fields between linked objects.
    In order to specify objects and fields that you want to keep in sync, you
    need to implement 'get_synced_objs' and 'get_synced_fields' methods.
    """

    def get_synced_objs(self):
        raise NotImplementedError()

    def get_synced_fields(self):
        raise NotImplementedError()

    def save(self, *args, **kwargs):
        from ralph.ui.views.common import SAVE_PRIORITY
        changes = []
        for obj in self.get_synced_objs():
            for f in self.get_synced_fields():
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
            obj.save(sync_fields=False, priority=SAVE_PRIORITY)
            fields_synced_signal.send_robust(sender=self, changes=changes)
