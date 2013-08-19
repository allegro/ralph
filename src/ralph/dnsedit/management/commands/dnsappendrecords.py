#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand
from powerdns.models import Record, RECORD_TYPES

from bob.csvutil import UnicodeReader
from ralph.dnsedit.util import get_domain


class Error(Exception):
    pass


class DisallowedRecordTypeError(Error):
    """Trying to create a record which is not a of allowed types."""


class IncorrectLengthRowError(Error):
    """Trying to unpack row."""


class EmptyRecordValueError(Error):
    """Trying to create record from empty values."""


class Command(BaseCommand):
    """
    Append DNS records form csv file to existing Domain
    record should be in this format::

        name;type;content
    """

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        for filename in args:
            self.handle_single(filename)

    def handle_single(self, filename):
        print('Importing DNS records from {}...'.format(filename))
        with open(filename, 'rb') as f:
            for i, value in enumerate(UnicodeReader(f), 1):
                if len(value) != 4:
                    raise IncorrectLengthRowError(
                        'CSV row {} has {} elements, should be 3'.format(
                            i,
                            len(value),
                        )
                    )
                name, type, content = value
                if not all((name, type, content)):
                    raise EmptyRecordValueError(
                        'Record fields can not be empty',
                    )
                if type not in RECORD_TYPES:
                    raise DisallowedRecordTypeError(
                        'Record type {} is not allowed. Use:\n {}'.format(
                            type,
                            RECORD_TYPES,
                        ),
                    )
                self.create_record(name, type, content)

    def create_record(self, name, type, content):
        domain = get_domain(name)
        record, created = Record.objects.get_or_create(
            domain=domain,
            name=name,
            type=type,
            content=content,
        )
        print('Record {}: {} IN {} {} (zone {})'.format(
            'created' if created else 'exists',
            record.name,
            record.type,
            record.content,
            record.domain,
        ))
        return created
