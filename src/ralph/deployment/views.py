#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.http import (HttpResponse, HttpResponseNotFound,
    HttpResponseForbidden)
from lck.django.common import remote_addr, render

from ralph.deployment.models import (Deployment, DeploymentStatus, FileType,
    PrebootFile)


def get_current_deployment(request):
    ip = remote_addr(request)
    deployment = None
    try:
        deployment = Deployment.objects.get(ip=ip,
            status=DeploymentStatus.in_deployment)
    except Deployment.DoesNotExist:
        if request.user.is_superuser and request.GET.get('ip'):
            ip = request.GET.get('ip')
            deployment = Deployment.objects.get(ip=ip,
                status=DeploymentStatus.in_deployment)
    return deployment


def get_response(pbf):
    if pbf.file:
        if settings.USE_XSENDFILE:
            response = HttpResponse(content_type='application/force-download')
            response['X-Sendfile'] = pbf.file.path
        else:
            # FIXME: in Django 1.5 use StreamingHttpResponse
            with open(pbf.file.path) as file:
                response = HttpResponse(file.read(),
                    content_type='application/force-download')
        response['Content-Length'] = pbf.file.size
    else:
        response = HttpResponse(pbf.raw_config, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % pbf.name
    return response


def preboot_raw_view(request, file_name):
    try:
        deployment = get_current_deployment(request)
        pbf = deployment.preboot.files.get(name=file_name)
        return get_response(pbf)
    except (AttributeError, Deployment.DoesNotExist, PrebootFile.DoesNotExist,
        PrebootFile.MultipleObjectsReturned):
        pass
    if file_name in ('boot', 'boot_ipxe', 'boot.ipxe'):
        return render(request, 'deployment/localboot.txt', locals(),
            mimetype='text/plain')
    return HttpResponseNotFound()


def preboot_type_view(request, file_type):
    try:
        ftype = FileType.from_name(file_type)
    except ValueError:
        return HttpResponseNotFound()
    try:
        deployment = get_current_deployment(request)
        pbf = deployment.preboot.files.get(ftype=ftype)
        return get_response(pbf)
    except (AttributeError, Deployment.DoesNotExist, PrebootFile.DoesNotExist,
        PrebootFile.MultipleObjectsReturned):
        pass
    if ftype is FileType.boot_ipxe:
        return render(request, 'deployment/localboot.txt', locals(),
            mimetype='text/plain')
    return HttpResponseNotFound()


def preboot_complete_view(request):
    try:
        deployment = get_current_deployment(request)
        deployment.status = DeploymentStatus.resolved_fixed
        deployment.save()
        return HttpResponse()
    except Deployment.DoesNotExist:
        return HttpResponseNotFound('No deployment can be completed at this '
                                    'point.')
