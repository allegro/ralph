#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import zlib

def get_base64_compressed_data(data):
    try:
        data = base64.b64decode(data)
    except TypeError:
        pass
    finally:
        try:
            data = zlib.decompress(data)
        except zlib.error:
            pass
        else:
            return data
