#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Discovers machines in networks specified in the admin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
from optparse import make_option
import textwrap

from django.core.management.base import CommandError
from django.core.management.base import BaseCommand

from ralph.discovery.models import IPAddress
from ralph.business.models import Venture


class Command(BaseCommand):
    """
    Upload ip addresses data from file to database
    """
    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option(
            '-f', '--file',
            dest='file',
            default=None,
            help="File with data",
        ),
    )

    def handle(self, *args, **options):
        """Dispatches the request to either direct, interactive execution
        or to asynchronous processing using the queue."""
        if not options.get('file'):
            raise CommandError('Input file not specified')
        venture = None
        with open(options.get('file'), 'r') as f:
            for line in f.readlines():
                line = line.replace('\n', '')
                if not line:
                    continue
                if not re.search('\d.*\.\d.*\.\d.*\.\d.*', line):
                    venture_name = line.replace(':', '')
                    try:
                        venture = Venture.objects.get(
                            symbol=line.replace(':', ''),
                        )
                    except Venture.DoesNotExist:
                        venture = None
                        print ("{0} does not exist".format(venture_name))
                elif venture:
                    ip_address = IPAddress.objects.get_or_create(
                        address=line
                    )[0]
                    if not ip_address.venture:
                        ip_address.venture = venture
                    ip_address.save()
