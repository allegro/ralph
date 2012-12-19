#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ralph.deployment.util import get_next_free_hostname
from ralph.discovery.models import DataCenter


class Command(BaseCommand):
    args = '<dc name>'
    help = 'Return next host name for specified data center.'

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Please specify the DC name.')
        try:
            hostname = get_next_free_hostname(args[0])
        except DataCenter.DoesNotExist:
            raise CommandError("Specified data center doesn't exists.")
        if not hostname:
            raise CommandError("Couldn't determine the next host name.")
        self.stdout.write("Next host name: %s\n" % hostname)

