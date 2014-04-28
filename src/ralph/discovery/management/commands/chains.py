#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Django manage.py command to list all configured plug-in chains."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand

from ralph.util import plugin


class Command(BaseCommand):

    """Lists all plugin chains available."""
    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        """Dispatches the request to either direct, interactive execution
        or to asynchronous processing using Rabbit."""
        chains = sorted(plugin.BY_REQUIREMENTS.keys())
        for chain in chains:
            print(chain, "chain:")
            reqs = sorted("{} -> {}".format(", ".join(sorted(k)) or 'START',
                                            ", ".join(sorted(v))) for k, v in
                          plugin.BY_REQUIREMENTS[chain].iteritems())
            for req in reqs:
                print("-", req)
