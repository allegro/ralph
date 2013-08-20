#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from bob.csvutil import UnicodeReader
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from powerdns.models import Domain, Record


class Error(Exception):
    pass


class IncorrectLengthRowError(Error):
    """Trying to unpack row."""


class Command(BaseCommand):
    """Append PTR DNS records form csv file to existing Domain
    record should be in this format:
    name;type;content;domain name
    """

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        for filename in args:
            self.handle_single(filename)

    def handle_single(self, filename):
        records = []
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
                records.append({'name': name, 'content': content})
            self.create_records(records)

    def create_records(self, records):
        no_ptr_records, errors = [], []
        for record in records:
            revname = '.'.join(
                reversed(record['content'].split('.'))
            ) + '.in-addr.arpa'
            domain_name = '.'.join(
                list(reversed(record['content'].split('.')))[1:]
            ) + '.in-addr.arpa'

            # when records will be created
            domain, domain_created = Domain.objects.get_or_create(name=domain_name)
            print('prepare name={}, content={}, domain={}, ip={}'.format(
                revname,
                record['name'],
                domain,
                record['content'],
            ))
            try:
                record_ptr, record_created = Record.objects.get_or_create(
                    name=revname,
                    content=record['name'],
                    type='PTR',
                    domain=domain
                )
            except IntegrityError:
                errors.append((revname, record['name'], domain, record['content']))
            if record_created:
                no_ptr_records.append(record)
                print('Created record')
            else:
                print('Record exist')
        print('Ip address without PTR: {}'.format(
            [record['content'] for record in no_ptr_records])
        )
        print('Created: {}'.format(len(no_ptr_records)))
        print('Fail: {}'.format(len(errors)))
        print('Failed records: {}'.format([error for error in errors]))
