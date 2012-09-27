#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from ralph.business.models import Venture, VentureRole

SLUG_VALIDATION_REGEX = re.compile(r'^[a-z]{1}[a-z0-9_]*[a-z0-9]{1}$')

def slug_validation(data):
    result = SLUG_VALIDATION_REGEX.match(data)
    return bool(result)

def invalid_ventures():
    ventures = Venture.objects.all()
    result = []
    for venture in ventures:
        if not slug_validation(venture.symbol):
            result.append({'name': venture.name, 'id': venture.id, 'symbol': venture.symbol})
    return result

def invalid_roles():
    roles = VentureRole.objects.all()
    result = []
    for role in roles:
        if not slug_validation(role.name):
            result.append({'name': role.name, 'id': role.id})
    return result