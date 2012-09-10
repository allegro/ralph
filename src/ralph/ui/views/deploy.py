#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from django.contrib import messages

from ralph.discovery.models import Device
from ralph.ui.views.common import BaseMixin
from ralph.ui.forms import DeploymentForm


class Deployment(BaseMixin, CreateView):
    form_class = DeploymentForm
    template_name = 'ui/device_deploy.html'

    def get_success_url(self):
        return self.request.path

    def get_template_names(self):
        return [self.template_name]

    def get_initial(self):
        return {
            'device': Device.objects.get(id=int(self.kwargs['device'])),
        }

    def form_valid(self, form):
        model = form.save(commit=False)
        model.user = self.request.user
        model.save()
        messages.success(self.request, "Deployment initiated.")
        return HttpResponseRedirect(
                self.request.path + '/../../info/%d' % model.device.id)
