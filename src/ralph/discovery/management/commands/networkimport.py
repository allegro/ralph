#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.core.management.base import BaseCommand
from bob.csvutil import UnicodeReader

from ralph.discovery.models import (
    DataCenter,
    Device,
    DeviceType,
    Environment,
    Network,
    NetworkTerminator,
)


class Error(Exception):
    pass


class IncorrectLengthRowError(Error):

    """Trying to unpack row."""


class EmptyRecordValueError(Error):

    """Trying to create network from empty values."""


class TerminatorDoesNotExist(Error):

    """  """


class DataCenterDoesNotExist(Error):

    """  """


class EnvironmentDoesNotExist(Error):

    """  """


class RackDoesNotExist(Error):

    """  """


class Command(BaseCommand):

    """Append Networks from csv file, record should be in this format:
    network name;address;terminator name;data center name;environment;rack name
    """

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = True

    def handle(self, *args, **options):
        for filename in args:
            self.handle_single(filename)

    def handle_single(self, filename):
        print('Importing Network from {}...'.format(filename))
        with open(filename, 'rb') as f:
            for i, value in enumerate(UnicodeReader(f), 1):
                if len(value) != 6:
                    raise IncorrectLengthRowError(
                        'CSV row {} have {} elements, should be 6'.format(
                            i, len(value)
                        )
                    )
                (
                    name,
                    address,
                    terminator_name,
                    data_center_name,
                    environment_name,
                    rack_name
                ) = value
                if not all(
                    (
                        name,
                        address,
                        terminator_name,
                        data_center_name,
                        environment_name,
                        rack_name,
                    )
                ):
                    raise EmptyRecordValueError(
                        'Record fields can not be empty',
                    )
                self.create_network(
                    name, address, terminator_name, data_center_name,
                    environment_name, rack_name, i,
                )

    def create_network(
        self, name, address, terminator_name, data_center_name,
        environment_name, rack_name, row
    ):
        print('# Trying to create network `{}` {}'.format(name, address))
        try:
            terminator = NetworkTerminator.objects.get(name=terminator_name)
        except NetworkTerminator.DoesNotExist:
            raise TerminatorDoesNotExist(
                'Terminator with name `{}` specified in row {} does not exist'.
                format(terminator_name, row)
            )

        try:
            data_center = DataCenter.objects.get(name=data_center_name)
        except DataCenter.DoesNotExist:
            raise DataCenterDoesNotExist(
                'DataCenter with name `{}` specified in row {} does not exist'.
                format(data_center_name, row)
            )

        try:
            environment = Environment.objects.get(name=environment_name)
        except Environment.DoesNotExist:
            raise EnvironmentDoesNotExist(
                'Environment with name `{}` specified in row {} does '
                'not exist'.format(environment_name, row)
            )

        try:
            rack_name = Device.objects.get(
                name=rack_name,
                model__type=DeviceType.rack,
                dc=data_center
            )
        except Device.DoesNotExist:
            raise RackDoesNotExist(
                'Rack with name `{}` in `{}` data center, specified in row {}'
                ' does not exist'.format(rack_name, data_center_name, row)
            )

        network, created = Network.objects.get_or_create(
            name=name,
            address=address,
            data_center=data_center,
            environment=environment,
        )
        if created:
            network.terminators = [terminator, ]
            network.racks = [rack_name, ]
            network.save()
            print('  + Network `{}` {} successfully created'.format(
                name, address)
            )
        else:
            print('  - Network `{}` {} already exist'.format(name, address))
