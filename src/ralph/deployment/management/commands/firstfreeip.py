#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ralph.deployment.util import get_first_free_ip
from ralph.discovery.models import Network


class Command(BaseCommand):
    args = '<network name>'
    help = 'Return first free IP for specified network.'

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Please specify the network name.')
        try:
            ip = get_first_free_ip(args[0])
        except Network.DoesNotExist:
            raise CommandError("Specified network doesn't exists.")
        if not ip:
            raise CommandError("Couldn't determine the first free IP.")
        self.stdout.write("First free IP: %s\n" % ip)
