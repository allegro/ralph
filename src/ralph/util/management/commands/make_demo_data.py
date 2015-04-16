# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pkg_resources
import textwrap
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import BaseCommand

from ralph.util.demo import registry, DemoRunner


class Command(BaseCommand):
    """Create a example data."""

    help = textwrap.dedent(__doc__).strip()
    # TODO: add database option
    option_list = BaseCommand.option_list + (
        make_option(
            '--flush',
            action='store_true',
            dest='flush',
            default=False,
            help='Flush database before generate.'
        ),
        make_option(
            '-d',
            dest='fixtures',
            action='append',
            type='str',
            default=[],
            help='Fixtures to apply',
        ),
        make_option(
            '-i',
            dest='interactive',
            action='store_true',
            default=False,
            help='Select fixtures interactively',
        ),
    )

    def handle(self, *args, **options):
        flush = options.get('flush')
        fixtures = options.get('fixtures')
        interactive = options.get('interactive')
        for package in pkg_resources.iter_entry_points(
            group='ralph.demo_data_module'
        ):
            package.load()
        demo = None
        if flush:
            self.flush()
        if interactive:
            selected = self.select_demos()
            if not selected:
                return
            demo = DemoRunner(selected)
        elif fixtures:
            demo = DemoRunner(fixtures)
        else:
            demo = DemoRunner(registry.keys())
        if demo:
            demo.run()

    def select_demos(self):
        """Helper method for interactive mode. User select demo data by
        simple menu."""
        keys = []
        for pos, (key, demo) in enumerate(sorted(registry.items())):
            self.stdout.write('{}) {} ({}), required: {}\n'.format(
                pos, demo.title, demo.name, ', '.join(demo.required or [])
            ))
            keys.append(key)
        choices = input('Please select demo data (eg.: 1, 4, 6): ')
        if isinstance(choices, int):
            choices = [choices]
        return [keys[idx] for idx in choices]

    def flush(self):
        # TODO: select database to flush
        self.stdout.write('Flush database..\n')
        call_command('flush', interactive=False)
        self.stdout.write('Flush finished.\n')
