#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import factory
from factory.django import DjangoModelFactory

from ralph.deployment.models import MassDeployment, Preboot, Deployment
from ralph.discovery.tests.util import DeviceFactory


class DeploymentFactory(DjangoModelFactory):
    FACTORY_FOR = Deployment

    device = factory.SubFactory(DeviceFactory)
    mac = "000000000000"
    ip = ""


class MassDeploymentFactory(DjangoModelFactory):
    FACTORY_FOR = MassDeployment


class PrebootFactory(DjangoModelFactory):
    FACTORY_FOR = Preboot
