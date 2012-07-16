#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
import ralph.cmdb.models as db

admin.site.register([db.CI,db.CIType,db.CILayer,db.CIRelation,db.CIAttribute, 
    db.CIAttributeValue])
