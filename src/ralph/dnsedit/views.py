# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from lck.django.common import remote_addr
from django.shortcuts import get_object_or_404

from ralph.account.models import ralph_permission
from ralph.discovery.models import DataCenter, Environment
from ralph.dnsedit.models import DHCPServer
from ralph.dnsedit.dhcp_conf import (
    generate_dhcp_config_entries,
    generate_dhcp_config_head,
    generate_dhcp_config_networks,
)


DHCP_DISABLE_NETWORKS_VALIDATION = getattr(
    settings, 'DHCP_DISABLE_NETWORKS_VALIDATION', False,
)


@ralph_permission()
def dhcp_synch(request):
    address = remote_addr(request)
    server = get_object_or_404(DHCPServer, ip=address)
    server.last_synchronized = datetime.datetime.now()
    server.save()
    return HttpResponse('OK', content_type='text/plain')


def _get_params(request):
    dc_names = request.GET.get('dc', '')
    if dc_names:
        dc_names = dc_names.split(',')
    else:
        dc_names = []
    env_names = request.GET.get('env', '')
    if env_names:
        env_names = env_names.split(',')
    else:
        env_names = []
    return dc_names, env_names


@ralph_permission()
def dhcp_config_entries(request):
    dc_names, env_names = _get_params(request)
    if dc_names and env_names:
        return HttpResponseForbidden('Only DC or ENV mode available.')
    data_centers = []
    for dc_name in dc_names:
        try:
            dc = DataCenter.objects.get(name__iexact=dc_name)
        except DataCenter.DoesNotExist:
            return HttpResponseNotFound(
                "Data Center `%s` does not exist." % dc_name
            )
        else:
            data_centers.append(dc)
    environments = []
    for env_name in env_names:
        try:
            env = Environment.objects.get(name__iexact=env_name)
        except Environment.DoesNotExist:
            return HttpResponseNotFound(
                "Environment `%s` does not exist." % env_name
            )
        else:
            environments.append(env)
    return HttpResponse(
        generate_dhcp_config_entries(
            data_centers=data_centers,
            environments=environments,
            disable_networks_validation=DHCP_DISABLE_NETWORKS_VALIDATION,
        ),
        content_type="text/plain",
    )


@ralph_permission()
def dhcp_config_networks(request):
    dc_names, env_names = _get_params(request)
    if dc_names and env_names:
        return HttpResponseForbidden('Only DC or ENV mode available.')
    data_centers = []
    for dc_name in dc_names:
        try:
            dc = DataCenter.objects.get(name__iexact=dc_name)
        except DataCenter.DoesNotExist:
            return HttpResponseNotFound(
                "Data Center `%s` does not exist." % dc_name
            )
        else:
            data_centers.append(dc)
    environments = []
    for env_name in env_names:
        try:
            env = Environment.objects.get(name__iexact=env_name)
        except Environment.DoesNotExist:
            return HttpResponseNotFound(
                "Environment `%s` does not exist." % env_name
            )
        else:
            environments.append(env)
    return HttpResponse(
        generate_dhcp_config_networks(
            data_centers=data_centers,
            environments=environments,
        ),
        content_type='text/plain',
    )


@ralph_permission()
def dhcp_config_head(request):
    server_address = request.GET.get('server')
    if not server_address:
        server_address = remote_addr(request)
    dhcp_server = get_object_or_404(DHCPServer, ip=server_address)
    return HttpResponse(
        generate_dhcp_config_head(
            dhcp_server=dhcp_server,
        ),
        content_type='text/plain',
    )
