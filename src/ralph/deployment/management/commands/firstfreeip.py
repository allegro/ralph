#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ralph.deployment.util import get_firstfreeip


class Command(BaseCommand):
    args = '<dc name>'
    help = 'Return first free IP for specified network.'

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Please specify the network name.')
        status, ip, error_msg = get_firstfreeip(args[0])
        if not status:
            raise CommandError(error_msg)
        self.stdout.write("First free IP: %s\n" % ip)

