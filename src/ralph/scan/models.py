#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db
from lck.django.common.models import WithConcurrentGetOrCreate


class ScanSummary(db.Model, WithConcurrentGetOrCreate):

    """
    For every IP address we prescanned we add scan summary record which holds
    checksum and ignored checksum. When the user press `Ignore change` button
    we store the current checksum as ignored one.
    """

    job_id = db.CharField(unique=True, max_length=36)
    previous_checksum = db.CharField(max_length=32)
    false_positive_checksum = db.CharField(
        blank=True,
        null=True,
        max_length=32,
        verbose_name="Ignored checksum",
    )
    created = db.DateTimeField(auto_now=False, auto_now_add=True)
    modified = db.DateTimeField(auto_now=True, auto_now_add=True)
