# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.business.models import Venture, VentureRole


def all_ventures():
    yield '', '---------'
    for v in Venture.objects.filter(show_in_ralph=True).order_by('path'):
        yield (
            v.id,
            "%s[%s] %s" % (
                '\u00A0' * 4 * v.path.count('/'),  # u00A0 == 'no-break space'
                v.symbol,
                v.name,
            )
        )


def all_roles():
    yield '', '---------'
    for r in VentureRole.objects.order_by(
        '-venture__is_infrastructure', 'venture__name',
        'parent__parent__name', 'parent__name', 'name'
    ):
        yield r.id, '{} / {}'.format(r.venture.name, r.full_name)
