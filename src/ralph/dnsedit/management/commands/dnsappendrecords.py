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


class DomainNotExists(Error):
    """Trying to get Domain from name."""


class DisallowedRecordType(Error):
    """Trying to create a record which is not a of allowed types."""


class Command(BaseCommand):
    """Import DNS records form csv file"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        for filename in args:
            self.handle_single(filename)

    def handle_single(self, filename):
        print('Importing DNS records from {}...'.format(filename))
        with open(filename, 'rb') as f:
            for name, type, content, domain_name in UnicodeReader(f):
                if type in RECORD_TYPES:
                    domain = self.get_domain(domain_name)
                    self.create_record(type, domain, name, content)
                else:
                    raise DisallowedRecordType(
                        'Record type {} is not allowed. Use:\n {}'.format(
                            type,
                            RECORD_TYPES,
                        )
                    )

    def get_domain(self, domain_name):
        try:
            domain = Domain.objects.get(name=domain_name)
        except Domain.DoesNotExist:
            raise DomainNotExists('Domain %s not found.' % domain_name)
        return domain

    def create_record(self, type, domain, name, content):
        record, created = Record.objects.get_or_create(
            domain=domain,
            name=name,
            type=type,
            content=content,
        )
        if created:
            print('Record created: {} IN {} {} {}'.format(
                record.name,
                record.type,
                record.content,
                record.domain,
            )
            )
        else:
            print('Record exist: {} IN {} {} {}'.format(
                record.name,
                record.type,
                record.content,
                record.domain
            )
            )
        return created
