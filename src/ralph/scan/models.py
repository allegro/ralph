#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db
from lck.django.common.models import WithConcurrentGetOrCreate


class ScanSummary(db.Model, WithConcurrentGetOrCreate):
    job_id = db.CharField(unique=True, max_length=36)
    previous_checksum = db.CharField(max_length=32)
    false_possitive_checksum = db.CharField(
        blank=True,
        null=True,
        max_length=32,
    )
    created = db.DateTimeField(auto_now=False, auto_now_add=True)
    modified = db.DateTimeField(auto_now=True, auto_now_add=True)

