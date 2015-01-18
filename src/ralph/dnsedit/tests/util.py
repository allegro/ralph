# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from factory.django import DjangoModelFactory
from powerdns.models import Domain, Record

from ralph.dnsedit.models import DHCPEntry


class DHCPEntryFactory(DjangoModelFactory):

    FACTORY_FOR = DHCPEntry


class DNSDomainFactory(DjangoModelFactory):

    FACTORY_FOR = Domain


class DNSRecordFactory(DjangoModelFactory):

    FACTORY_FOR = Record
