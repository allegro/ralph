#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unicodedata

from django.conf import settings
from django.dispatch.dispatcher import Signal
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from lck.django.common.models import MACAddressField

from ralph.cmdb.models import CI
from ralph.cmdb.models_audits import Auditable, DeploymentStatus, create_issue
from ralph.cmdb.models_common import getfunc
from ralph.discovery.models import Device


# This signal is fired, when deployment is accepted in Bugtracker.
# note, that you should manually change deployment statuses.
deployment_accepted = Signal(providing_args=['deployment_id'])


def normalize_owner(owner):
    owner = owner.name.lower().replace(' ', '.')
    return unicodedata.normalize('NFD', owner).encode('ascii', 'ignore')

def get_technical_owner(device):
    owners = device.venture.technical_owners()
    if owners:
        return normalize_owner(owners[0])

def get_business_owner(device):
    owners = device.venture.business_owners()
    if owners:
        return normalize_owner(owners[0])


class Deployment(Auditable):
    device = models.ForeignKey(Device)
    mac =  MACAddressField()
    status = models.IntegerField(choices=DeploymentStatus(),
                                 default=DeploymentStatus.open.id)
    ip = models.IPAddressField(verbose_name=_("IP address"))
    hostname = models.CharField(verbose_name=_("hostname"), max_length=255)
    img_path = models.CharField(verbose_name=_("image path"), max_length=255)
    kickstart_path = models.CharField(verbose_name=_("kickstart path"),
                                      max_length=255)
    venture = models.ForeignKey('business.Venture', verbose_name=_("venture"),
                                null=True)
    venture_role = models.ForeignKey('business.VentureRole', null=True,
                                     verbose_name=_("role"))
    done_plugins = models.TextField(verbose_name=_("done plugins"),
                                    blank=True, default='')

    def fire_issue(self):
        s = settings.ISSUETRACKERS['default']['OPA']
        ci = None
        bowner = None
        towner = None
        bowner = get_business_owner(self.device)
        towner = get_technical_owner(self.device)
        params = dict(
            ci_uid = CI.get_uid_by_content_object(self.device),
            # FIXME: doesn't check if CI even exists
            description = 'Please accept',
            summary = 'Summary',
            ci=ci,
            technical_assigne=towner,
            business_assignee=bowner,
            template=s['TEMPLATE'],
            issue_type=s['ISSUETYPE'],
        )
        getfunc(create_issue)(type(self), self.id, params)


class DeploymentPooler(models.Model):
    key = models.CharField(max_length=255, null=False)
    date = models.DateTimeField(null=False)
    checked = models.BooleanField(default=False)


@receiver(deployment_accepted, dispatch_uid='ralph.cmdb.deployment_accepted')
def handle_deployment_accepted(sender, deployment_id, **kwargs):
    # sample deployment accepted signal code.
    pass


# Import all the plugins
import ralph.deployment.plugins
