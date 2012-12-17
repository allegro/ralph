#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
from collections import namedtuple
import re
import zlib


Eth = namedtuple('Eth', 'label mac speed')


def untangle(seq):
    if isinstance(seq, (list, tuple, set)):
        for elem in seq:
            for e in untangle(elem):
                yield e
    else:
        yield seq


BASE64_ALPHABET = re.compile(b'^[A-Za-z0-9+/\s]*={0,2}$', flags=re.MULTILINE)


def uncompress_base64_data(data):
    """
    Return `data` decompressed with zlib. If `data` is valid Base64, decode it
    before decompression. If decompression fails, return raw data.
    """
    if not data:
        return data
    if BASE64_ALPHABET.match(data):
        try:
            data = base64.b64decode(data)
        except TypeError:
            pass  # padding error
    try:
        data = zlib.decompress(data)
    except zlib.error:
        pass
    return data
