#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    """Generate configuration for the DHCP server."""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, server_address=None, *args, **options):
        # Avoid an import loop
        from ralph.dnsedit.dhcp_conf import generate_dhcp_config
        print(generate_dhcp_config(server_address=server_address))
