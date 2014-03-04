#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ralph.deployment.util import get_next_free_hostname
from ralph.discovery.models import Environment


class Command(BaseCommand):
    args = '<environment name>'
    help = 'Return next hostname for specified environment.'

    def handle(self, dc_name=None, *args, **options):
        if not dc_name:
            raise CommandError('Please specify the DC name.')
        try:
            env = Environment.objects.get(name=dc_name)
        except Environment.DoesNotExist:
            raise CommandError("Specified data center doesn't exists.")
        hostname = get_next_free_hostname(env)
        if not hostname:
            raise CommandError("Couldn't determine the next host name.")
        self.stdout.write("Next host name: %s\n" % hostname)
