#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404

from ralph.deployment.models import MultipleDeploymentInitialData
from ralph.deployment.util import get_nexthostname, get_firstfreeip
from ralph.discovery.models import Device, Network
from ralph.ui.views.common import BaseMixin, Base
from ralph.ui.forms import (
    DeploymentForm, PrepareMultipleDeploymentForm, MultipleDeploymentForm,
)


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
                '%s/../../../../deployment/multiple/define/%s/' % (
                    self.request.path, multiple_deployment.pk,
                )
            )
        messages.error(self.request, "Please correct the errors.")
        return super(
            PrepareMultipleServersDeployment, self
        ).get(*args, **kwargs)


class MultipleServersDeployment(Base):
    template_name = 'ui/multiple_deploy.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(
            MultipleServersDeployment, self
        ).get_context_data(*args, **kwargs)
        ret.update({
            'form': self.form
        })
        return ret

    def get(self, *args, **kwargs):
        multiple_deployment = get_object_or_404(
            MultipleDeploymentInitialData, id=kwargs.get('deployment')
        )
        reserved_hostnames = []
        reserved_ip_addresses = []
        csv_rows = []
        for row in multiple_deployment.csv.strip().split("\n"):
            cols = row.split(";")
            hostname = ""
            ip = ""
            try:
                rack = Device.objects.get(sn=cols[1])
                status, next_hostname, _ = get_nexthostname(
                    rack.dc, reserved_hostnames=reserved_hostnames
                )
                if status:
                    hostname = next_hostname
                    reserved_hostnames.append(hostname)
                try:
                    network = Network.objects.get(rack=rack.name)
                    status, new_ip, _ = get_firstfreeip(
                        network.name,
                        reserved_ip_addresses=reserved_ip_addresses
                    )
                    if status:
                        ip = new_ip
                        reserved_ip_addresses.append(ip)
                except Network.DoesNotExist:
                    pass
            except Device.DoesNotExist:
                pass
            cols.insert(0, ip)
            cols.insert(0, hostname)
            csv_rows.append(
                ";".join(cols)
            )
        self.form = MultipleDeploymentForm(
            initial={'csv': "\n".join(csv_rows)}
        )
        return super(
            MultipleServersDeployment, self
        ).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = MultipleDeploymentForm(self.request.POST)
        if self.form.is_valid():
            pass
        messages.error(self.request, "Please correct the errors.")
        return super(
            MultipleServersDeployment, self
        ).get(*args, **kwargs)
