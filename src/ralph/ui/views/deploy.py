#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import cStringIO

from django.views.generic import CreateView
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404

from ralph.deployment.models import MassDeployment as MassDeploymentModel
from ralph.deployment.util import (
    get_next_free_hostname, get_first_free_ip, create_deployments
)
from ralph.discovery.models import DeviceType, Device, Network, DataCenter
from ralph.ui.views.common import BaseMixin, Base
from ralph.ui.forms import (
    DeploymentForm, PrepareMassDeploymentForm, MassDeploymentForm,
)
from ralph.util.csvutil import UnicodeReader, UnicodeWriter


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


class PrepareMassDeployment(Base):
    template_name = 'ui/mass_deploy.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(
            PrepareMassDeployment, self
        ).get_context_data(*args, **kwargs)
        ret.update({
            'form': self.form,
            'action_name': 'Next step'
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = PrepareMassDeploymentForm()
        return super(
            PrepareMassDeployment, self
        ).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = PrepareMassDeploymentForm(self.request.POST)
        if self.form.is_valid():
            csv = self.form.cleaned_data['csv'].strip()
            mass_deployment = MassDeploymentModel(csv=csv)
            mass_deployment.created_by = self.request.user.get_profile()
            mass_deployment.save()
            return HttpResponseRedirect(
                '/ui/deployment/mass/define/%s/' % mass_deployment.pk
            )
        messages.error(self.request, "Please correct the errors.")
        return super(
            PrepareMassDeployment, self
        ).get(*args, **kwargs)


class MassDeployment(Base):
    template_name = 'ui/mass_deploy.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(
            MassDeployment, self
        ).get_context_data(*args, **kwargs)
        ret.update({
            'form': self.form,
            'action_name': 'Deploy'
        })
        return ret

    def get(self, *args, **kwargs):
        mass_deployment = get_object_or_404(
            MassDeploymentModel, id=kwargs.get('deployment'),
            is_done=False
        )
        reserved_hostnames = []
        reserved_ip_addresses = []
        new_csv_rows = []
        csv_rows = UnicodeReader(cStringIO.StringIO(
            mass_deployment.csv.strip()
        ))
        for raw_cols in csv_rows:
            cols = []
            for col in raw_cols:
                cols.append(" %s " % col.strip())
            hostname = ""
            ip = ""
            rack = None
            try:
                network = Network.objects.get(name=cols[2].strip())
                new_ip = get_first_free_ip(
                    network.name,
                    reserved_ip_addresses=reserved_ip_addresses
                )
                if new_ip:
                    ip = new_ip
                    reserved_ip_addresses.append(ip)
                try:
                    rack = network.racks.order_by('name')[0]
                    dc_name = rack.dc if rack.dc else ""
                    if (rack.parent and rack.parent.model and
                        rack.parent.model.type == DeviceType.data_center):
                        dc_name = rack.parent.name
                    try:
                        next_hostname = get_next_free_hostname(
                            dc_name, reserved_hostnames=reserved_hostnames
                        )
                        if next_hostname:
                            hostname = next_hostname
                            reserved_hostnames.append(hostname)
                    except DataCenter.DoesNotExist:
                        pass
                except IndexError:
                    pass
            except Network.DoesNotExist:
                pass
            cols.insert(0, " %s " % rack.sn if rack else " ")
            cols.insert(0, " %s " % ip)
            cols.insert(0, " %s " % hostname)
            new_csv_rows.append(cols)
        csv_string = cStringIO.StringIO()
        UnicodeWriter(csv_string).writerows(new_csv_rows)
        self.form = MassDeploymentForm(
            initial={'csv': csv_string.getvalue()}
        )
        return super(
            MassDeployment, self
        ).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        mass_deployment = get_object_or_404(
            MassDeploymentModel, id=kwargs.get('deployment'),
            is_done=False
        )
        self.form = MassDeploymentForm(self.request.POST)
        if self.form.is_valid():
            create_deployments(
                self.form.cleaned_data['csv'],
                self.request.user,
                mass_deployment
            )
            mass_deployment.generated_csv = self.form.data['csv'].strip()
            mass_deployment.is_done = True
            mass_deployment.save()
            messages.success(self.request, "Deployment initiated.")
            return HttpResponseRedirect('/')
        messages.error(self.request, "Please correct the errors.")
        return super(
            MassDeployment, self
        ).get(*args, **kwargs)
