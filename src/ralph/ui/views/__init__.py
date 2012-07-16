# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from ralph.util.views import jsonify
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from ralph.discovery import tasks

from ralph.business.models import Venture
from ralph.discovery.models_device import Device
from ralph.discovery.models_network import Network
from ralph.account.models import Perm


@csrf_exempt
@jsonify
def typeahead_roles(request):
    venture_id = request.POST.get('venture')
    roles = [('', '---------')]
    if venture_id:
        venture = get_object_or_404(Venture, id=venture_id)
        roles.extend((r.id, unicode(r)) for r in venture.venturerole_set.all())
    return {
        'items': roles,
    }

@csrf_exempt
@jsonify
def unlock_field(request):
    device_id = request.POST.get('device', '')
    device = get_object_or_404(Device, id=device_id)
    field_name = request.POST.get('field', '')
    try:
        field = getattr(device, field_name + '_id')
    except AttributeError:
        try:
            field = getattr(device, field_name)
        except AttributeError:
            raise Http404("Wrong field name.")
    else:
        field_name = field_name + '_id'
    priorities = device.get_save_priorities()
    priorities[field_name] = 0
    device.update_save_priorities(priorities)
    device.save()
    return {}


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')


def discover(request):
    has_perm = request.user.get_profile().has_perm
    if not has_perm(Perm.run_discovery):
        raise Http404('Forbidden')
    ip = request.POST.get('ip', '')
    try:
        Network.from_ip(ip)
    except (IndexError, ValueError):
        raise Http404('No such address.')
    def data():
        yield 'Running discovery for %s\n' % ip
        for chunk in tasks.discover_single_synchro(ip):
            yield chunk
    response = HttpResponse(''.join(data()), content_type='text/plain')
    response['Cache-Control'] = 'no-cache'
    return response
