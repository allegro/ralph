#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple


Eth = namedtuple('Eth', 'label mac speed')

def untangle(seq):
    if isinstance(seq, (list, tuple, set)):
        for elem in seq:
            for e in untangle(elem):
                yield e
    else:
        yield seq
