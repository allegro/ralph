#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


size_divisor = dict(
    bytes = 1024 * 1024,
    B = 1024 * 1024,
    kilobytes = 1024,
    kB = 1024,
    KB = 1024,
    KiB = 1024,
    megabytes = 1,
    MB = 1,
    MiB = 1,
    gigabytes = 1/1024,
    GB = 1/1024,
    GiB = 1/1024,
)

speed_divisor = dict(
    Hz = 1024 * 1024,
    kHz = 1024,
    MHz = 1,
    GHz = 1/1024,
)
