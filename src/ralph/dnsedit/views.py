# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.http import HttpResponse, HttpResponseForbidden
from lck.django.common import remote_addr
from django.shortcuts import get_object_or_404

from ralph.discovery.models import DataCenter
from ralph.dnsedit.models import DHCPServer
from ralph.dnsedit.dhcp_conf import (
    generate_dhcp_config,
    generate_dhcp_config_head,
)
from ralph.ui.views.common import Base
from ralph.util import api


class Index(Base):
    template_name = 'dnsedit/index.html'
    section = 'dns'

    def __init__(self, *args, **kwargs):
        super(Index, self).__init__(*args, **kwargs)


def dhcp_synch(request):
    if not api.is_authenticated(request):
        return HttpResponseForbidden('API key required.')
    address = remote_addr(request)
    server = get_object_or_404(DHCPServer, ip=address)
    server.last_synchronized = datetime.datetime.now()
    server.save()
    return HttpResponse('OK', content_type='text/plain')


def dhcp_config(request):
    if not api.is_authenticated(request):
        return HttpResponseForbidden('API key required.')
    dc_name = request.GET.get('dc', '')
    dc = None
    if dc_name:
        try:
            dc = DataCenter.objects.get(name__iexact=dc_name)
        except DataCenter.DoesNotExist:
            pass
    server_address = remote_addr(request)
    return HttpResponse(
        generate_dhcp_config(
            server_address=server_address,
            dc=dc,
        ),
        content_type="text/plain",
    )


def dhcp_config_head(request):
    if not api.is_authenticated(request):
        return HttpResponseForbidden('API key required.')
    dc_name = request.GET.get('dc', '')
    dc = None
    if dc_name:
        try:
            dc = DataCenter.objects.get(name__iexact=dc_name)
        except DataCenter.DoesNotExist:
            pass
    server_address = remote_addr(request)
    return HttpResponse(
        generate_dhcp_config_head(
            server_address=server_address,
            dc=dc,
        ),
        content_type='text/plain',
    )

