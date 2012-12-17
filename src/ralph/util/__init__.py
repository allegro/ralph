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

from django.conf import settings
from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner, reorder_suite
from django.utils.importlib import import_module
from django.utils.unittest.loader import defaultTestLoader


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


class DiscoveryDjangoTestSuiteRunner(DjangoTestSuiteRunner):
    """
    A test suite runner that uses unittest2 test discovery.
    Courtesy of @carljm.
    """
    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = None
        discovery_root = settings.TEST_DISCOVERY_ROOT
        if test_labels:
            suite = defaultTestLoader.loadTestsFromNames(test_labels)
            # if single named module has no tests, do discovery within it
            if not suite.countTestCases() and len(test_labels) == 1:
                suite = None
                discovery_root = import_module(test_labels[0]).__path__[0]
        if suite is None:
            suite = defaultTestLoader.discover(
                discovery_root,
                top_level_dir=settings.CURRENT_DIR,
            )
        if extra_tests:
            for test in extra_tests:
                suite.addTest(test)
        return reorder_suite(suite, (TestCase,))
