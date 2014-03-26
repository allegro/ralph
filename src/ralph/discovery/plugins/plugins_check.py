# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util import plugin
from ralph.discovery.models import IPAddress
from ralph.discovery.models_history import DiscoveryWarning


@plugin.register(chain='postprocess', requires=[])
def plugins_check(ip, **kwargs):
    ip = str(ip)
    try:
        ipaddr = IPAddress.objects.select_related().get(address=ip)
    except IPAddress.DoesNotExist:
        return False, 'no address.', kwargs
    plugins = kwargs.get('successful_plugins', '')
    if ipaddr.last_plugins != plugins:
        DiscoveryWarning(
            message="Successful plugins changed from [%s] to [%s]." % (
                ipaddr.last_plugins,
                plugins,
            ),
            plugin=__name__,
            device=ipaddr.device,
            ip=ip,
        ).save()
        ipaddr.last_plugins = plugins
        ipaddr.save()
    return True, plugins, kwargs
