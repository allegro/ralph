# -*- coding: utf-8 -*-
import textwrap
from importlib.metadata import entry_points

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Show configuration for hooks."""

    help = textwrap.dedent(__doc__).strip()

    def handle(self, *args, **kwargs):
        self.stdout.write("Hooks:")
        for key, active_variant in settings.HOOKS_CONFIGURATION.items():
            self.stdout.write("\n{}:".format(key))
            for ep in entry_points(group=key):
                ending = ""
                if active_variant == ep.name:
                    ending += self.style.NOTICE(" (active)")
                ending += "\n"
                self.stdout.write("\t {} [{}]".format(ep.name, ep.dist.name), ending=ending)
