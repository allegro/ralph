#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
from optparse import make_option
import sys

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db.models import Q
import xlwt

from ralph.util.csvutil import UnicodeWriter
from ralph.util import pricing
from ralph.business.models import Venture
from ralph.discovery.models import DeviceType, ReadOnlyDevice


def field(field_name):
    return lambda dev: unicode(getattr(dev, field_name) or '')

def subfield(field_name, subfield_name):
    return lambda dev: unicode(
            (getattr(getattr(dev, field_name), subfield_name)
                if getattr(dev, field_name) else None)
            or ''
        )
def first_subfield(field_name, subfield_name):
    return lambda dev: unicode(
            (getattr(getattr(dev, field_name).all()[0], subfield_name)
                if getattr(dev, field_name).count() else None)
            or ''
        )

def device_type(dev):
    return DeviceType.DescFromID(
            (dev.model.type if dev.model else None)
            or DeviceType.unknown.id
        ).title()

def missing_warning(field_name, message):
    return lambda dev: '' if getattr(dev, field_name).count() else message

def edit_url(dev):
    site = Site.objects.order_by('id')[0]
    return xlwt.Formula('HYPERLINK("http://%s/ui/search/info/%d)";"Edit")' %
        site.domain, dev.id)

def position(dev):
    return dev.get_position()

REPORTS = {
    '': [
            ('Device ID', field('id')),
            ('Name', field('name')),
            ('IP Address', first_subfield('ipaddress_set', 'address')),
            ('Data Center', field('dc')),
            ('Device Type', device_type),
            ('Venture', subfield('venture', 'name')),
            ('Role', subfield('venture_role', 'full_name')),
            ('Remarks', field('remarks')),
            ('Disk Warning', missing_warning('storage_set', 'No disk!')),
            ('CPU Warning', missing_warning('processor_set', 'No CPU!')),
            ('Memory Warning', missing_warning('memory_set', 'No memory!')),
            ('Edit URL', edit_url),
        ],
    'inventory': [
            ('Device ID', field('id')),
            ('Data Center', field('dc')),
            ('Rack', field('rack')),
            ('Position', position),
            ('Parent', subfield('parent', 'name')),
            ('Name', field('name')),
            ('Serial Number', field('sn')),
            ('Barcode', field('barcode')),
            ('Model', field('model')),
            ('Remarks', field('remarks')),
        ],
    'serials': [
            ('Name', field('name')),
            ('Data Center', field('dc')),
            ('Barcode', field('barcode')),
            ('Serial Number', field('sn')),
            ('Venture', subfield('venture', 'name')),
            ('Quoted Price', field('cached_price')),
            ('Cost', lambda d: '%.2f' % pricing.get_device_cost(d)),
            ('Model', field('model')),
            ('Remarks', field('remarks')),
    ]
}


class Command(BaseCommand):
    """Prepare a report"""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = False
    option_list = BaseCommand.option_list + (
            make_option('--output', dest='output', default=None,
                help='Where to write the report'),
            make_option('--format', dest='format', default='csv',
                help='Output format. Either csv or xls.',
                choices=['csv', 'xls']),
            make_option('--venture', dest='venture', default=None,
                help='Limit the report to specific venture'),
            make_option('--data-center', dest='dc', default=None,
                help='Limit the report to specific data center'),
    )

    def handle(self, report_name='', dc=None, format='csv',
               venture=None, output=None, **options):
        try:
            report = REPORTS[report_name]
        except KeyError:
            sys.stderr.write("Invalid report name, available report names are:\n%s\n" %
                             ', '.join('"%s"' % r for r in REPORTS))
            sys.exit(1)
        query = ReadOnlyDevice.objects.distinct()
        if venture:
            v = Venture.objects.get(Q(name__iexact=venture) | Q(symbol__iexact=venture))
            query = query.filter(venture=v)
        if dc:
            query = query.filter(dc_iexact=dc)
        if format == 'csv':
            if output:
                f = open(output, 'wb')
            else:
                f = sys.stdout
            writer = UnicodeWriter(f)
            writer.writerow([title for (title, func) in report])
            def get_rows(query, report):
                for dev in query.select_related(depth=2):
                    yield [func(dev) for (title, func) in report]
            writer.writerows(get_rows(query, report))
        elif format == 'xls':
            if not output:
                sys.stderr.write('Output file name is required for xls format.\n')
                sys.exit(1)
            workbook = xlwt.Workbook()
            def one_venture(v, workbook, query, report):
                worksheet = workbook.add_sheet(v.symbol.encode('ascii', 'ignore').replace('/', ' '))
                for i, (title, func) in enumerate(report):
                    worksheet.write(0, i, title)
                for i, dev in enumerate(query.filter(venture=v).select_related(depth=2)):
                    for j, (title, func) in enumerate(report):
                        value = func(dev)
                        worksheet.write(i+1, j, value)
            if venture:
                one_venture(v, workbook, query, report)
            else:
                for v in Venture.objects.filter(show_in_ralph=True):
                    one_venture(v, workbook, query, report)
            workbook.save(output)

