# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime


from django.http import HttpResponse, HttpResponseForbidden
from ralph.dnsedit.models import DHCPServer
from ralph.dnsedit.util import generate_dhcp_config
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
    address = request.META['REMOTE_ADDR']
    server, created = DHCPServer.objects.get_or_create(ip=address)
    server.last_synchronized = datetime.datetime.now()
    server.save()
    return HttpResponse('OK', content_type='text/plain')


def dhcp_config(request):
    if not api.is_authenticated(request):
        return HttpResponseForbidden('API key required.')
    return HttpResponse(generate_dhcp_config(), content_type="text/plain")
