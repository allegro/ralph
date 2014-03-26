#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand
from bob.csvutil import UnicodeReader
from optparse import make_option

from ralph.business.models import BusinessSegment, ProfitCenter, Venture


class Error(Exception):
    pass


class IncorrectLengthRowError(Error):

    """Trying to unpack row."""


class EmptyRecordValueError(Error):

    """Trying to create network from empty values."""


class VentureDoesNotExistError(Error):

    """Trying to get ventures."""


class Command(BaseCommand):

    """Import Profit Center from csv file, record should be in this format:
    venture id;profit center name;description
    """
    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option(
            '--connect_business_segment',
            action='store_true',
            default=False,
            help='Connect venture to existing Profit Center and '
            'Business Segment',
        ),
    )
    requires_model_validation = True

    def handle(self, *args, **options):
        if not args:
            print('You must specify filename to import!')
        for filename in args:
            self.handle_single(filename, **options)

    def handle_single(self, filename, **options):
        if options['connect_business_segment']:
            connect_business_segment = True
        else:
            connect_business_segment = False
        print('Importing information from {}...'.format(filename))
        with open(filename, 'rb') as f:
            self.not_found_ventures = []
            self.not_found_profit_centers = set()
            self.not_found_business_segments = set()
            for i, value in enumerate(UnicodeReader(f), 1):
                if len(value) != 3:
                    raise IncorrectLengthRowError(
                        'CSV row {} have {} elements, should be 3'.format(
                            i, len(value)
                        )
                    )
                if not connect_business_segment:
                    venture_id, profit_center, description = value
                    venture = self.get_venture(venture_id, i)
                    if not venture:
                        continue
                    else:
                        profit_center, created = ProfitCenter.objects.get_or_create(  # noqa
                            name=profit_center or 'Other'
                        )
                        profit_center.description = description or 'Other'
                        profit_center.save()
                        venture.profit_center = profit_center
                        venture.save()
                        print(
                            'profit center {} joined to venture {}'.format(
                                profit_center, venture.name
                            )
                        )
                else:
                    venture_id, profit_center_name, business_segment_name = value   # noqa
                    venture = self.get_venture(venture_id, i)
                    if not venture:
                        continue
                    else:
                        profit_center = self.get_profit_center(
                            profit_center_name, i,
                        )
                        business_segment = self.get_business_segment(
                            business_segment_name, i,
                        )
                        if profit_center:
                            venture.profit_center = profit_center
                        if business_segment:
                            venture.business_segment = business_segment
                        venture.save()
            print("Ventures with ids {} don't exist".format(
                [v for v in self.not_found_ventures]
            ))
            if connect_business_segment:
                print("Business Segments with name {} does not exist".format(
                    [v for v in self.not_found_business_segments]
                ))
                print("Profit Center with name {} does not exist".format(
                    [v for v in self.not_found_profit_centers]
                ))

    def get_venture(self, venture_id, row_number):
        venture = None
        try:
            venture = Venture.objects.get(id=venture_id)
        except Venture.DoesNotExist:
            print(
                'Venture with id `{}` specified in row {}'
                ' does not exist'.format(venture_id, row_number)
            )
            self.not_found_ventures.append(venture_id)
        return venture

    def get_profit_center(self, profit_center_name, row_number):
        profit_center = None
        try:
            profit_center = ProfitCenter.objects.get(
                name=profit_center_name,
            )
        except ProfitCenter.DoesNotExist:
            print(
                'Profit Center with name `{}` specified in row {}'
                ' does not exist'.format(profit_center_name, row_number)
            )
            self.not_found_profit_centers.add(profit_center_name)
        return profit_center

    def get_business_segment(self, business_segment_name, row_number):
        business_segment = None
        try:
            business_segment = BusinessSegment.objects.get(
                name=business_segment_name,
            )
        except BusinessSegment.DoesNotExist:
            print(
                'Business segment with name `{}` specified in'
                ' row {} does not exist'.format(
                    business_segment_name, row_number,
                )
            )
            self.not_found_business_segments.add(business_segment_name)
        return business_segment
