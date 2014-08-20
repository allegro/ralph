#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import TemplateView
from lck.django.common import render, redirect

from ralph.business.models import Venture


SYNERGY_URL_BASE = settings.SYNERGY_URL_BASE


class Index(TemplateView):
    template_name = 'business/index.html'

    def get_context_data(self, **kwargs):
        return {'CURRENCY': settings.CURRENCY}


def show_ventures(request, venture_id=None):
    if venture_id == 'search':
        if request.method != 'POST':
            return redirect(request, '/business/ventures/')
        search = request.POST['search']
        if not search:
            return redirect(request, '/business/ventures/')
        template = 'business/show_ventures.html'
        ventures = Venture.objects.filter(name__icontains=search).order_by(
            'name')
    elif venture_id:
        venture = Venture.objects.get(pk=venture_id)
        subventures = Venture.objects.filter(parent=venture).order_by('name')
        template = 'business/show_venture.html'
    else:
        ventures = Venture.objects.filter(parent=None).order_by('name')
        template = 'business/show_ventures.html'
    side_ventures = Venture.objects.filter(parent=None).order_by('name')
    synergy_url_base = SYNERGY_URL_BASE
    return render(request, template, locals())
