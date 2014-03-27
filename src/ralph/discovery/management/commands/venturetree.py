#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
import re

from django.core.management.base import BaseCommand
from ralph.business.models import Venture


class Command(BaseCommand):

    """Generate a tree of all ventures in a dot format."""

    help = textwrap.dedent(__doc__).strip()
    requires_model_validation = False
    option_list = BaseCommand.option_list

    def handle(self, **options):
        def norm(v):
            return re.sub(r'[^a-zA-Z0-9]', '_', v.symbol).lower()
        print('digraph Ventures {')
        print(' overlap=prism;')
        print(' root [label="Ventures"];')
        for v in Venture.objects.all():
            for c in v.child_set.all():
                print(' %s -> %s;' % (norm(v), norm(c)))
            if v.parent is None:
                print(' root -> %s;' % norm(v))
            attrs = {
                'label': '%s\\n[%s]' % (v.name, v.symbol),
                'shape': 'box' if v.show_in_ralph else 'ellipse',
                'style': 'filled' if v.is_infrastructure else '',
            }
            a = ','.join('%s="%s"' % a for a in attrs.iteritems())
            print((' %s [%s];' % (norm(v), a)).encode('utf8'))
        print('}')
