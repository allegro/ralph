# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from powerdns.models import Record

from ralph.discovery.models import DataCenter


def get_nexthostname(dc_name):
    try:
        dc = DataCenter.objects.get(name=dc_name)
    except DataCenter.DoesNotExist:
        return False, "", "Specified data center doesn't exists."
    templates = dc.hosts_naming_template.split("|")
    for template in templates:
        match = re.search('<([0-9]+),([0-9]+)>', template)
        if not match:
            return False, "", "Incorrect hosts names template in DC: %s" % (
                dc_name
            )
        min_number = int(match.group(1))
        max_number = int(match.group(2))
        number_len = len(match.group(2))
        regex = template.replace(
            match.group(0),
            "%s[0-9]{%s}" % (str(min_number)[0], number_len - 1)
        )
        next_number = min_number
        try:
            record = Record.objects.filter(
                domain__name__iregex=regex
            ).order_by('-domain__name')[0]
            name_match = re.search(
                template.replace(
                    match.group(0),
                    "(%s[0-9]{%s})" % (str(min_number)[0], number_len - 1)
                ),
                record.domain.name
            )
            next_number = int(name_match.group(1)) + 1
            if next_number > max_number:
                continue
        except IndexError:
            pass
        next_hostname = template.replace(
            match.group(0), "{0:%s}" % number_len
        ).format(next_number).replace(" ", "0")
        return True, next_hostname, ""
    return False, "", "Couldn't determine the next host name."


def get_nextip(network_name):
    pass

