#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin

from ralph.integration.models import RoleIntegration


class RoleIntegrationInline(admin.TabularInline):
    model = RoleIntegration

