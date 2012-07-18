#!/usr/bin/env python
import os
import sys

def main():
    os.environ["DJANGO_SETTINGS_MODULE"] = "ralph.settings"

    from django.core.management import execute_from_command_line

    sys.argv[0] = 'ralph'
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
