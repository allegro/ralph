# -*- coding: utf-8 -*-
import textwrap

import pkg_resources
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Show configuration for hooks."""
    help = textwrap.dedent(__doc__).strip()

    def handle(self, *args, **kwargs):
        self.stdout.write("Hooks:")
        for key, active_variant in settings.HOOKS_CONFIGURATION.items():
            self.stdout.write("\n{}:".format(key))
            for ep in pkg_resources.iter_entry_points(key):
                ending = ''
                if active_variant == ep.name:
                    ending += self.style.NOTICE(" (active)")
                ending += '\n'
                self.stdout.write(
                    "\t {} [{}]".format(ep.name, ep.dist.project_name),
                    ending=ending
                )
