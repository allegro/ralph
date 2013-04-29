#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Common models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db
from django.db.utils import DatabaseError
from django.contrib.auth.models import User
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
