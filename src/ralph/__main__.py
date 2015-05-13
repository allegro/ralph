#!/usr/bin/env python
import os
import sys


def main(settings_module='ralph.settings'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


def dev():
    main('ralph.settings.dev')


def test():
    main('ralph.settings.test')


if __name__ == '__main__':
    main()
