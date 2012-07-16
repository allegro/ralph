#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
from optparse import make_option
import sys

from django.core.management.base import BaseCommand
from django.db.models import Q

from ralph.util.csvutil import UnicodeReader
from ralph.discovery.models import Device

class Command(BaseCommand):
    """Import a report"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
            make_option('--fields', dest='fields', default=None,
                help='List of fields in the imported file'),
            make_option('--delimiter', dest='delimiter', default=b',',
                help='Delimiter used in the imported file'),
    )

    def handle(self, filename, fields='', delimiter=b',', **options):
        fields = [field.strip() for field in fields.split(',')]
        with open(filename, 'rb') as f:
            for row in UnicodeReader(f, delimiter=delimiter):
                data = dict(zip(fields, row))
                try:
                    dev_id = int(data['id'])
                except (ValueError, KeyError):
                    continue
                if not dev_id:
                    continue
                try:
                    dev = Device.objects.get(id=dev_id)
                except Device.DoesNotExist:
                    sys.stderr.write("Device with id=%r doesn't exist!\n" % dev_id)
                    continue
                for field, value in data.iteritems():
                    if field in ('id', ''):
                        continue
                    if value in ('None', ''):
                        value = None
                    if value is None and field in ('remarks',):
                        value = ''
                    print('%r.%s = %r' % (dev, field, value))
                    setattr(dev, field, value)
                    dev.save(priority=50)


