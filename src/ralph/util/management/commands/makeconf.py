#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ralph
import stat
import sys
import textwrap

from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):

    """Create a default configuration file."""

    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option('-g', '--global',
                    action='store_true',
                    dest='global',
                    default=False,
                    help="Use /etc instead of the current user's home directory."),
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help="Rewrite the config file if already exists."),
        make_option('-u', '--user',
                    action='store_true',
                    dest='user',
                    default=False,
                    help="User specified path for settings"),
    )

    requires_model_validation = False

    def handle(self, *args, **options):
        if options['global']:
            return self.makeconf('/etc/ralph', options['force'])
        if options['user']:
            try:
                path = args[0]
            except IndexError:
                sys.stderr.write('Path is not specified, '
                                 'enter the correct path\n\n')
                sys.stderr.flush()
                sys.exit(2)
            else:
                return self.makeconf(path, options['force'])
        return self.makeconf('~/.ralph', options['force'])

    def makeconf(self, ralph_dir, force=False):
        ralph_dir = os.path.expanduser(ralph_dir)
        if not os.path.exists(ralph_dir):
            try:
                os.mkdir(ralph_dir, 0700)
            except (IOError, OSError):
                sys.stderr.write(
                    'Not enough rights to create {}. Ask your administrator '
                    'to create it for you.\n'.format(ralph_dir)
                )
                sys.stderr.flush()
                sys.exit(1)
        else:
            os.chmod(ralph_dir, stat.S_IRWXU)
        orig_settings_path = os.sep.join((os.path.dirname(ralph.__file__),
                                          'settings.py'))
        new_settings_path = os.sep.join((ralph_dir, 'settings'))
        if not force and os.path.exists(new_settings_path):
            sys.stderr.write(
                'Configuration file at {} already exists. '
                'Use makeconf -f to overwrite.\n'.format(new_settings_path)
            )
            sys.stderr.flush()
            sys.exit(2)
        with open(orig_settings_path) as orig_settings:
            with open(new_settings_path, 'w') as settings:
                do_write = False
                for line in orig_settings.readlines():
                    if do_write:
                        if line.startswith('# </template>'):
                            break
                        settings.write(line)
                    elif line.startswith('# <template>'):
                        do_write = True
        os.chmod(new_settings_path, stat.S_IRUSR | stat.S_IWUSR)
