# -*- coding: utf-8 -*-

"""
Common errors for whole Scan application.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class Error(Exception):
    """Errors during the scan."""


class AuthError(Error):
    """"Authentication error."""


class NoQueueError(Error):
    """No discovery queue defined."""


class NotConfiguredError(Error):
    """Somethings not configured"""


class NoMatchError(Error):
    """No match."""


class ConnectionError(Error):
    """Connection error."""


class NoLanError(Error):
    """No LAN error."""


class SSHConsoleError(Error):
    """SSH console error."""


class TreeError(Error):
    """xml tree error"""


class DeviceError(Error):
    """somethings wrong with device"""

