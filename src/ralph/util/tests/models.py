# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db

from ralph.util.models import WithCustomAttributes


class MyDevice(WithCustomAttributes):

    name = db.CharField(max_length = 32)

    def __unicode__(self):
        return self.name
