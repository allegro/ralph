# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from ralph.discovery.models import DataCenter, Device


def get_nexthostname(dc_name):
    #import pdb
    #pdb.set_trace()
    try:
        dc = DataCenter.objects.get(name=dc_name)
    except DataCenter.DoesNotExist:
        return False, "", "Specified data center doesn't exists."
    match = re.search('{0?:([0-9]+)}', dc.hosts_naming_template)
    if not match:
        return False, "", "Not supported host name template."
    regex = dc.hosts_naming_template.replace(
        match.group(0), "[0-9]{%s}" % match.group(1)
    )
    next_num = 1
    try:
        device = Device.objects.filter(
            dc__iexact=dc.name, name__iregex=regex
        ).order_by('-name')[0]
        match = re.search(
            dc.hosts_naming_template.replace(
                match.group(0), "([0-9]{%s})" % match.group(1)
            ),
            device.name
        )
        if match:
            next_num = int(match.group(1)) + 1
    except IndexError:
        pass
    return True, dc.hosts_naming_template.format(next_num), ""

