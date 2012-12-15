#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from django.contrib import messages

from ralph.deployment.models import MultipleDeploymentInitialData
from ralph.discovery.models import Device
from ralph.ui.views.common import BaseMixin, Base
from ralph.ui.forms import DeploymentForm, PrepareMultipleDeploymentForm


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
            self.request.path + '/../../info/%d' % model.device.id
        )


class PrepareMultipleServersDeployment(Base):
    template_name = 'ui/prepare_multiple_deploy.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(
            PrepareMultipleServersDeployment, self
        ).get_context_data(*args, **kwargs)
        ret.update({
            'form': self.form
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = PrepareMultipleDeploymentForm()
        return super(
            PrepareMultipleServersDeployment, self
        ).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = PrepareMultipleDeploymentForm(self.request.POST)
        if self.form.is_valid():
            csv = self.form.cleaned_data['csv'].strip()
            multiple_deployment = MultipleDeploymentInitialData(csv=csv)
            multiple_deployment.created_by = self.request.user.get_profile()
            multiple_deployment.save()
            return HttpResponseRedirect(
                '%s/../../../deployment/multiple/define/%s/' % (
                    self.request.path, multiple_deployment.pk,
                )
            )
        messages.error(self.request, "Please correct the errors.")
        return super(
            PrepareMultipleServersDeployment, self
        ).get(*args, **kwargs)
