import os
import sys


def main():
    if 'cross_validator' not in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'ralph.cross_validator.settings'
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
