#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ralph.settings")

    from django.core.management import execute_from_command_line

    sys.argv[0] = 'python -m ralph'
    execute_from_command_line(sys.argv)
