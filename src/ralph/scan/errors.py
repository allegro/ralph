# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class Error(Exception):
    """Errors during the scan."""


class NoQueueError(Error):
    """No discovery queue defined."""


class NotConfiguredError(Error):
    """Somethings not configured"""


class NoMatchError(Error):
    """No match."""
<<<<<<< HEAD
=======


class ConnectionError(Error):
    """Connection error."""
>>>>>>> 93b66c1cbe8e3c6f932af715aea18f04cf24c22f
