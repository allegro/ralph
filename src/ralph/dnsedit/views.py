# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime


from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden
from ralph.dnsedit.models import DHCPServer
from ralph.dnsedit.util import generate_dhcp_config
from ralph.ui.views.common import Base


class Index(Base):
    template_name = 'dnsedit/index.html'
    section = 'dns'

    def __init__(self, *args, **kwargs):
        super(Index, self).__init__(*args, **kwargs)


def is_authorized(request):
    username = request.GET.get('username')
    api_key = request.GET.get('api_key')
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    return user and user.api_key == api_key


def dhcp_synch(request):
    if not is_authorized(request):
        return HttpResponseForbidden('API key required.')
    address = request.META['REMOTE_ADDR']
    server = DHCPServer.get_or_create(ip=address)
    server.last_synchronized = datetime.datetime.now()
    return HttpResponse('OK', content_type='text/plain')


def dhcp_config(request):
    if not is_authorized(request):
        return HttpResponseForbidden('API key required.')
    return HttpResponse(generate_dhcp_config(), content_type="text/plain")
