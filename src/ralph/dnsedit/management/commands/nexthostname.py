#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ralph.deployment.util import get_nexthostname


class Command(BaseCommand):
    args = '<dc name>'
    help = 'Return next host name for specified data center.'

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Please specify the DC name.')
        status, hostname, error_msg = get_nexthostname(args[0])
        if not status:
            raise CommandError(error_msg)
        self.stdout.write("Next host name: %s\n" % hostname)

