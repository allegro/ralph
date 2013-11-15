# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr

from ralph.discovery.models import Network


def find_network(network_spec):
    """Returns network object by network address."""
    try:
        address = str(ipaddr.IPNetwork(network_spec))
    except ValueError:
        network = Network.objects.get(name=network_spec)
    else:
        network = Network.objects.get(address=address)
    return network

