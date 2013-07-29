# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class Error(Exception):
    """Errors during the scan."""


class NoQueueError(Error):
    """No discovery queue defined."""


class NoMacError(Error):
    """No MAC address."""


class NoMatchError(Error):
    """No match."""

