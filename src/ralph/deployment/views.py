#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import timedelta
import json

from django.conf import settings
from django.template import Template, Context
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.db.models import Q
from lck.django.common import remote_addr

from ralph.account.models import ralph_permission
from ralph.deployment.models import (
    Deployment,
    DeploymentStatus,
    FileType,
    PrebootFile,
)
from ralph.discovery.models import IPAddress, Device
from ralph.discovery.tasks import run_next_plugin


def get_current_deployment(request):
    ip = remote_addr(request)
    deployment = None
    try:
        deployment = Deployment.objects.get(
            ip=ip,
            status=DeploymentStatus.in_progress
        )
    except Deployment.DoesNotExist:
        ip = request.GET.get('ip')
        if ip:
            try:
                deployment = Deployment.objects.get(
                    ip=ip,
                    status=DeploymentStatus.in_progress
                )
            except Deployment.DoesNotExist:
                pass
    return deployment


def get_response(pbf, deployment):
    """Return a HTTP response for the given preboot file object.

    For an attachment, return its contents as-is. If settings.USE_XSENDFILE is
    used, use that instead of sending raw data.

    For raw configuration, render it as a Django template and serve it."""
    if pbf.file:
        if settings.USE_XSENDFILE:
            response = HttpResponse(content_type='application/force-download')
            response['X-Sendfile'] = pbf.file.path
        else:
            # FIXME: in Django 1.5 use StreamingHttpResponse
            with open(pbf.file.path) as file:
                response = HttpResponse(
                    file.read(),
                    content_type='application/force-download'
                )
        response['Content-Length'] = pbf.file.size
    else:
        raw_config = pbf.raw_config.replace('\r\n', '\n').replace('\r', '\n')
        raw_config = '{%load raw_config%}' + raw_config
        tpl = Template(raw_config)
        ctxt = Context(dict(
            # preboot file
            filename=pbf.name,
            filetype=pbf.ftype.name,
            # deployment
            mac=deployment.mac,
            ip=deployment.ip,
            hostname=deployment.hostname,
            venture=deployment.venture.symbol,
            venture_role=deployment.venture_role.name,
        ))
        response = HttpResponse(tpl.render(ctxt), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % pbf.name
    return response


def _preboot_view(request, file_name=None, file_type=None):
    assert file_name or file_type
    deployment = get_current_deployment(request)
    message = "Not found"
    if deployment:
        try:
            if file_name:
                pbf = deployment.preboot.files.get(name=file_name)
            else:
                try:
                    ftype = FileType.from_name(file_type)
                except ValueError:
                    return HttpResponseNotFound("Unknown file type given.")
                pbf = deployment.preboot.files.get(ftype=ftype)
        except PrebootFile.DoesNotExist:
            if file_name:
                message = "File %s not found for this server." % file_name
            else:
                message = "No file of type %s for this server." % file_type
        else:
            return get_response(pbf, deployment)
    else:
        message = "No deployment for this server."
    return HttpResponseNotFound(message)


def preboot_raw_view(request, file_name):
    return _preboot_view(request, file_name=file_name)


def preboot_type_view(request, file_type):
    return _preboot_view(request, file_type=file_type)


def preboot_complete_view(request):
    deployment = get_current_deployment(request)
    if not deployment:
        return HttpResponseNotFound(
            "No deployment can be completed at this moment."
        )
    deployment.status = DeploymentStatus.done
    deployment.save()
    try:
        ip_address = deployment.device.ipaddress_set.get(
            is_management=True,
        )
        run_next_plugin(
            {'ip': ip_address.address},
            ('discovery', 'postprocess'),
            interactive=False,
            after=timedelta(minutes=10),
        )
    except IPAddress.DoesNotExist:
        pass
    run_next_plugin(
        {'ip': deployment.ip},
        ('discovery', 'postprocess'),
        interactive=False,
        after=timedelta(minutes=10),
    )
    deployment.archive()
    return HttpResponse()


@ralph_permission()
def puppet_classifier(request):
    hostname = request.GET.get('hostname', '').strip()
    qs = Device.objects.filter(
        Q(name=hostname) |
        Q(ipaddress__hostname=hostname)
    ).distinct().select_related(*(
        [
            'venture',
            'department',
            'venture_role',
            'model',
            'model__group',
        ] + ['__'.join(['parent'] * i) for i in range(1, 6)]
    ))
    for device in qs[:1]:
        break
    else:
        raise Http404('Hostname %s not found' % hostname)
    location = device.get_position() or ''
    node = device.parent
    visited = set()
    while node and node not in visited:
        visited.add(node)
        name = node.name or '?'
        location = name + '__' + location if location else name
        node = node.parent
    department = None
    owners = []
    if device.venture:
        department = device.venture.get_department()
        ownerships = device.venture.all_ownerships()
        if hasattr(ownerships, 'select_related'):
            owners = ownerships.select_related()
    response = {
        'name': device.name,
        'device_id': device.id,
        'venture': device.venture.symbol if device.venture else None,
        'role': device.venture_role.full_name.replace(
            ' / ',
            '__',
        ) if device.venture_role else None,
        'department': department.name if department else None,
        'owners': [
            {
                'first_name': o.owner.first_name,
                'last_name': o.owner.last_name,
                'email': o.owner.email,
                'type': o.type,
            } for o in owners
        ],
        'verified': device.verified,
        'last_seen': device.last_seen.strftime('%Y-%m-%dT%H:%M:%S'),
        'model': device.model.name if device.model else None,
        'model_group': device.model.group.name if (
            device.model and
            device.model.group
        ) else None,
        'location': location,
        'properties': device.venture_role.get_properties(
            device,
        ) if device.venture_role else {},
        'property_types': device.venture_role.get_property_types(
            device,
        ) if device.venture_role else {},
        'data_center': device.dc,
        'rack': device.rack,
    }
    return HttpResponse(
        json.dumps(response),
        content_type='application/json; charset=utf-8',
    )
