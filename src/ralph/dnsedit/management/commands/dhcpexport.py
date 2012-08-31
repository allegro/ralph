#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand

from ralph.dnsedit.util import generate_dhcp_config


class Command(BaseCommand):
    """Generate configuration for the DHCP server."""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        print(generate_dhcp_config())
