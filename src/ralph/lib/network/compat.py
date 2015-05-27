# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six

if six.PY2:
    from ipaddr import(
        IPAddress,
        IPNetwork,
        IPv4Network,
        NetmaskValueError,
    )
else:
    from ipaddress import (
        ip_address as IPAddress,
        ip_network as IPNetwork,
        IPv4Network,
        NetmaskValueError
    )

__all__ = ['IPv4Network', 'IPAddress', 'IPNetwork', 'NetmaskValueError']
