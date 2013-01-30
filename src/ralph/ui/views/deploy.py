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
from lck.django.common.models import MACAddressField

from ralph.deployment.models import MassDeployment as MassDeploymentModel
from ralph.deployment.util import (
    create_deployments,
    get_first_free_ip,
    get_next_free_hostname,
)
from ralph.discovery.models import Device, Network, IPAddress
from ralph.ui.views.common import BaseMixin, Base, TEMPLATE_MENU_ITEMS
from ralph.ui.forms.deployment import (
    DeploymentForm,
    MassDeploymentForm,
    PrepareMassDeploymentForm,
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
        self.device = Device.objects.get(id=int(self.kwargs['device']))
        return {
            'device': self.device,
        }

    def form_valid(self, form):
        model = form.save(commit=False)
        model.user = self.request.user
        model.save()
        messages.success(self.request, "Deployment initiated.")
        return HttpResponseRedirect(
            self.request.path + '/../../info/%d' % model.device.id
        )

    def get_context_data(self, **kwargs):
        if not self.device.verified:
            messages.error(
                self.request,
                "{} - is not verified, you cannot "
                "deploy this device".format(self.device),
            )
        return {
            'form': kwargs['form'],
            'device': self.device
        }

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
        ret['template_menu_items'] = TEMPLATE_MENU_ITEMS
        ret['template_selected'] = 'servers'
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


def _find_device(mac):
    """Find the device to be re-used for this deployment. Return None if no
    matching device is found.
    """
    mac = MACAddressField.normalize(mac)
    try:
        return Device.admin_objects.get(ethernet__mac=mac)
    except Device.DoesNotExist:
        return None


def _find_network_ip(network_name, reserved_ip_addresses, device=None):
    """Find the network and IP address to be used for deployment.
    If ``device`` is specified, re-use an IP of that device that matches
    the specified network. If no network is specified, any IP matches.
    If no suitable network is found, ``Network.DoesNotExist`` is raised.
    If no suitable IP address is found, "" is returned for the IP.
    Never uses an IP that is in ``reserved_ip_addresses``. When an IP is
    found, it is added to ``reserved_ip_addresses``.
    """
    if network_name:
        network = Network.objects.get(name=network_name)
        if device:
            for ipaddress in device.ipaddress_set.filter(
                is_management=False,
                network=network,
            ).order_by('hostname', 'address'):
                ip = ipaddress.address
                if ip in reserved_ip_addresses:
                    continue
                reserved_ip_addresses.append(ip)
                return network, ip
        ip = get_first_free_ip(network.name, reserved_ip_addresses) or ''
        if ip:
            reserved_ip_addresses.append(ip)
        return network, ip
    if device:
        for ipaddress in device.ipaddress_set.filter(
            is_management=False,
        ).order_by('hostname', 'address'):
            ip = ipaddress.address
            if ip in reserved_ip_addresses:
                continue
            try:
                network = Network.from_ip(ip)
            except IndexError:
                continue
            reserved_ip_addresses.append(ip)
            return network, ip
    raise Network.DoesNotExist("No default network for this device")


def _find_hostname(network, reserved_hostnames, device=None, ip=None):
    """Find the host name for the deployed device. Reuse existing hostname if
    ``device`` and ``ip`` is specified.  Never pick a hostname that is in
    ``reserved_hostnames`` already.  If no suitable hostname found, return "",
    otherwise the returned hostname is added to ``reserved_hostnames`` list.
    """

    if device and ip:
        try:
            ipaddress = IPAddress.objects.get(address=ip)
        except IPAddress.DoesNotExist:
            pass
        else:
            if ipaddress.hostname:
                return ipaddress.hostname
    hostname = get_next_free_hostname(network.data_center, reserved_hostnames)
    if hostname:
        reserved_hostnames.append(hostname)
    return hostname or ""


class MassDeployment(Base):
    template_name = 'ui/mass_deploy.html'

    def __init__(self, *args, **kwargs):
        super(MassDeployment, self).__init__(*args, **kwargs)
        self.actions = []

    def get_context_data(self, *args, **kwargs):
        ret = super(MassDeployment, self).get_context_data(*args, **kwargs)
        ret.update({
            'form': self.form,
            'action_name': 'Deploy',
            'template_menu_items': TEMPLATE_MENU_ITEMS,
            'template_selected': 'servers',
            'actions': self.actions,
        })
        return ret

    def get(self, *args, **kwargs):
        mass_deployment = get_object_or_404(
            MassDeploymentModel,
            id=kwargs.get('deployment'),
            is_done=False,
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
            device = _find_device(cols[0])
            try:
                network, ip = _find_network_ip(
                    cols[2].strip(),
                    reserved_ip_addresses,
                    device,
                )
            except Network.DoesNotExist:
                pass
            else:
                hostname = _find_hostname(
                    network,
                    reserved_hostnames,
                    device,
                    ip,
                )
                for rack in network.racks.filter(
                    deleted=False
                ).order_by('name')[:1]:
                    break
                cols[2] = " %s " % network.name
            cols.insert(0, " %s " % rack.sn if rack else " ")
            cols.insert(0, " %s " % ip)
            cols.insert(0, " %s " % hostname)
            new_csv_rows.append(cols)
            if device:
                self.actions.append((
                    'warning',
                    "An old device %s will be re-used. Make sure it's not "
                    "used in production anymore!" % device,
                ))
                if device.deleted:
                    self.actions.append((
                        'info',
                        "Device %s will be undeleted." % device,
                    ))
                if device.ipaddress_set.exists():
                    self.actions.append((
                        'info',
                        "All DNS entries for IP addresses [%s] will be deleted." %
                        ', '.join(
                            ip.address for ip in device.ipaddress_set.all()
                        ),
                    ))
                    self.actions.append((
                        'info',
                        "All DHCP entries for IP addresses [%s] "
                        "will be deleted." % (
                            ', '.join(
                                ip.address for ip in device.ipaddress_set.all()
                            ),
                        ),
                    ))
                if device.ethernet_set.exists():
                    self.actions.append((
                        'info',
                        "All DHCP entries for  "
                        "MAC addresses [%s] will be deleted." % (
                            ', '.join(
                                eth.mac for eth in device.ethernet_set.all()
                            ),
                        ),
                    ))
                if device.disksharemount_set.exists():
                    self.actions.append((
                        'info',
                        "All disk shares mounted on %s will be disconnected "
                        "from it." % device,
                    ))
                self.actions.append((
                    'info',
                    "The uptime, operating system and software list for %s "
                    "will be reset." % device,
                ))
            else:
                if hostname:
                    self.actions.append((
                        'success',
                        "A new device %s will be created." % hostname,
                    ))
            if hostname and ip:
                self.actions.append((
                    'info',
                    "An A DNS entry for %s and %s will be created." %
                    (hostname, ip),
                ))
                self.actions.append((
                    'info',
                    "A PTR DNS entry for %s and %s will be created." %
                    (hostname, ip),
                ))
            if cols[0].strip() and ip:
                self.actions.append((
                    'info',
                    "A DHCP entry for %s and %s will be created." %
                    (cols[3], ip),
                ))
        csv_string = cStringIO.StringIO()
        UnicodeWriter(csv_string).writerows(new_csv_rows)
        self.form = MassDeploymentForm(
            initial={'csv': csv_string.getvalue()}
        )
        return super(MassDeployment, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        mass_deployment = get_object_or_404(
            MassDeploymentModel,
            id=kwargs.get('deployment'),
            is_done=False,
        )
        self.form = MassDeploymentForm(self.request.POST)
        if self.form.is_valid():
            create_deployments(
                self.form.cleaned_data['csv'],
                self.request.user,
                mass_deployment,
            )
            mass_deployment.generated_csv = self.form.data['csv'].strip()
            mass_deployment.is_done = True
            mass_deployment.save()
            messages.success(self.request, "Deployment initiated.")
            return HttpResponseRedirect('/')
        messages.error(self.request, "Please correct the errors.")
        return super(MassDeployment, self).get(*args, **kwargs)

