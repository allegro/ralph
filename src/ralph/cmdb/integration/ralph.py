#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from ralph.cmdb.integration.base import BaseImporter
from ralph.util import plugin
from ralph.cmdb import models as db
from ralph.discovery.models_history import HistoryChange


logger = logging.getLogger(__name__)

class AssetChangeImporter(BaseImporter):
    """ Ralph manual changes are registered as changes """

    @staticmethod
    @plugin.register(chain='cmdb_assets', requires=[])
    def assets(context):
        x = AssetChangeImporter()
        x.import_changes()
        return (True, 'Done', context)

    def import_changes(self):
        device_type = ContentType.objects.get(app_label="discovery", model="device")
        for x in HistoryChange.objects.filter(user_id__gt = 0, device__gt=0):
            try:
                ch = db.CIChange()
                ch.content_object = x
                ci = None
                ci = db.CI.objects.filter(object_id=x.device.id,
                        content_type=device_type).all()[0]
                ch.ci = ci
                ch.priority = db.CI_CHANGE_PRIORITY_TYPES.WARNING.id
                ch.time = x.date
                ch.message = x.comment or ''
                ch.type = db.CI_CHANGE_TYPES.DEVICE.id
                ch.save()
            except IntegrityError, e:
                logger.debug('Skipping already imported: %s' % x)


