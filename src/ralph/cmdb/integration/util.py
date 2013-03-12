#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from dateutil.parser import parse
from pytz import timezone


def strip_timezone(datestr):
    parsed = parse(datestr)
    return parsed.astimezone(timezone('Europe/Warsaw')).strftime('%Y-%m-%d %H:%M:%S')
