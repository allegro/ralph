#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
)
from django.template import Template, Context
from lck.django.common import remote_addr, render

from ralph.deployment.models import (
    Deployment,
    DeploymentStatus,
    FileType,
    PrebootFile,
)
from ralph.discovery.models import IPAddress
from ralph.discovery.tasks import discover_single


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


def preboot_raw_view(request, file_name):
    try:
        deployment = get_current_deployment(request)
        pbf = deployment.preboot.files.get(name=file_name)
        return get_response(pbf, deployment)
    except (AttributeError, Deployment.DoesNotExist, PrebootFile.DoesNotExist,
            PrebootFile.MultipleObjectsReturned):
        pass
    if file_name in ('boot', 'boot_ipxe', 'boot.ipxe'):
        return render(
            request,
            'deployment/localboot.txt',
            locals(),
            mimetype='text/plain'
        )
    return HttpResponseNotFound()


def preboot_type_view(request, file_type):
    try:
        ftype = FileType.from_name(file_type)
    except ValueError:
        return HttpResponseNotFound()
    try:
        deployment = get_current_deployment(request)
        pbf = deployment.preboot.files.get(ftype=ftype)
        return get_response(pbf, deployment)
    except (AttributeError, Deployment.DoesNotExist, PrebootFile.DoesNotExist,
            PrebootFile.MultipleObjectsReturned):
        pass
    if ftype is FileType.boot_ipxe:
        return render(
            request,
            'deployment/localboot.txt',
            locals(),
            mimetype='text/plain'
        )
    return HttpResponseNotFound()


def preboot_complete_view(request):
    try:
        deployment = get_current_deployment(request)
        deployment.status = DeploymentStatus.done
        deployment.save()
        try:
            ip_address = deployment.device.ipaddress_set.get(
                is_management=True,
            )
            discover_single.apply_async(
                args=[{'ip': ip_address.address}, ],
                countdown=600,  # 10 minutes
            )
        except IPAddress.DoesNotExist:
            pass
        discover_single.apply_async(
            args=[{'ip': deployment.ip}, ],
            countdown=600,  # 10 minutes
        )
        deployment.archive()
        return HttpResponse()
    except Deployment.DoesNotExist:
        return HttpResponseNotFound('No deployment can be completed at this '
                                    'point.')
