# -*- coding: utf-8 -*-
import textwrap

import pkg_resources
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Show configuration for entry points."""
    help = textwrap.dedent(__doc__).strip()

    def handle(self, *args, **kwargs):
        self.stdout.write("Entry points:")
        for key, active_variant in settings.ENTRY_POINTS_CONFIGURATION.items():
            self.stdout.write("\t{}:".format(key))
            for ep in pkg_resources.iter_entry_points(key):
                ending = '\n'
                try:
                    ep.load()
                except ImportError as e:
                    ending = self.style.ERROR(" (error: {})\n".format(e))
                if active_variant == ep.name:
                    ending = self.style.NOTICE(" (active)\n")
                self.stdout.write("\t\t" + ep.name, ending=ending)

