#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Model utilities and mixins."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db


class SavingUser(db.Model):
    class Meta:
        abstract = True

    def save(self, user=None, *args, **kwargs):
        self.saving_user = user
        return super(SavingUser, self).save(*args, **kwargs)
