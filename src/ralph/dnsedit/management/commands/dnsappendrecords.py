#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand
from powerdns.models import Domain, Record, RECORD_TYPES

from ralph.util.csvutil import UnicodeReader


class Error(Exception):
    pass


class DisallowedRecordTypeError(Error):
    """Trying to create a record which is not a of allowed types."""


class IncorrectLengthRowError(Error):
    """Trying to unpack row."""


class EmptyRecordValueError(Error):
    """Trying to create record from empty values."""


class Command(BaseCommand):
    """Append DNS records form csv file to existing Domain
    record should be in this format:
    name;type;content;domain name
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
                        'CSV row {} have {} elements, should be 4'.format(
                            i,
                            len(value),
                        )
                    )
                name, type, content, domain_name = value
                if not all((name, type, content, domain_name)):
                    raise EmptyRecordValueError('Record fields can not be empty')
                if type in RECORD_TYPES:
                    domain = Domain.objects.get(name=domain_name)
                    self.create_record(type, domain, name, content)
                else:
                    raise DisallowedRecordTypeError(
                        'Record type {} is not allowed. Use:\n {}'.format(
                            type,
                            RECORD_TYPES,
                        )
                    )

    def create_record(self, type, domain, name, content):
        record, created = Record.objects.get_or_create(
            domain=domain,
            name=name,
            type=type,
            content=content,
        )
        print('Record {}: {} IN {} {} {}'.format(
            'created' if created else 'exists',
            record.name,
            record.type,
            record.content,
            record.domain,
        ))
        return created
