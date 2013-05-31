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

from ralph.business.models import BusinessSegment, PricingCenter, Venture


class Error(Exception):
    pass


class IncorrectLengthRowError(Error):
    """Trying to unpack row."""


class EmptyRecordValueError(Error):
    """Trying to create network from empty values."""


class VentureDoesNotExistError(Error):
    """Trying to get ventures."""


class Command(BaseCommand):
    """Import Pricing Center from csv file, record should be in this format:
    venture id;pricing center name;description
    """
    help = textwrap.dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option(
            '--connect_business_segment',
            action='store_true',
            default=False,
            help='Connect venture to existing Pricing Center and '
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
            for i, value in enumerate(UnicodeReader(f), 1):
                if len(value) != 3:
                    raise IncorrectLengthRowError(
                        'CSV row {} have {} elements, should be 3'.format(
                            i, len(value)
                        )
                    )
                if not connect_business_segment:
                    venture_id, pricing_center, description = value
                    venture = self.get_venture(venture_id, i)
                    if not venture:
                        continue
                    else:
                        pricing_center, created = PricingCenter.objects.get_or_create(
                            name=pricing_center or 'Other'
                        )
                        pricing_center.description = description or 'Other'
                        pricing_center.save()
                        venture.pricing_center = pricing_center
                        venture.save()
                        print(
                            'pricing center {} joined to venture {}'.format(
                                pricing_center, venture.name
                            )
                        )
                else:
                    venture_id, pricing_center_name, business_segment_name = value
                    self.not_found_pricing_centers = []
                    self.not_found_business_segments = []
                    venture = self.get_venture(venture_id, i)
                    if not venture:
                        continue
                    else:
                        pricing_center = self.get_pricing_center(
                            pricing_center_name, i,
                        )
                        if not pricing_center:
                            continue
                        else:
                            business_segment = self.get_business_segment(
                                business_segment_name, i,
                            )
                            if not business_segment:
                                continue
                            else:
                                venture.pricing_center = pricing_center
                                venture.business_segment = business_segment
                                venture.save()
            print("Ventures with ids {} don't exist".format(
                [v for v in self.not_found_ventures]
            ))
            if connect_business_segment:
                print("Business Segments with name {} does not exist".format(
                    [v for v in self.not_found_business_segments]
                ))
                print("Pricing Center with name {} does not exist".format(
                    [v for v in self.not_found_pricing_centers]
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

    def get_pricing_center(self, pricing_center_name, row_number):
        pricing_center = None
        try:
            pricing_center = PricingCenter.objects.get(
                name=pricing_center_name,
            )
        except PricingCenter.DoesNotExist:
            print(
                'Pricing Center with name `{}` specified in row {}'
                ' does not exist'.format(pricing_center_name, row_number)
            )
            self.not_found_pricing_centers.append(pricing_center)
        return pricing_center

    def get_business_segment(self, business_segment_name, row_number):
        business_segment = None
        try:
            business_segment = BusinessSegment.objects.get(
                name=business_segment_name,
            )
        except BusinessSegment.DoesNotExist:
            print(
                'Business segment  with name `{}` specified in'
                ' row {} does not exist'.format(
                    business_segment_name, row_number,
                )
            )
            self.not_found_business_segments.append(business_segment)
        return business_segment
