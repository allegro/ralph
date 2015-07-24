#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import itertools
from uuid import uuid1

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from ralph.cmdb import models_changes, models_ci
from ralph.discovery import models_device


service_name_generator = itertools.cycle([
    'Backup systems', 'Load balancing', 'Databases'
])
env_name_generator = itertools.cycle([
    'prod', 'test', 'dev'
])


class CITypeFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIType
    name = factory.Sequence(lambda n: 'Name #{}'.format(n))


class CIFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CI

    @factory.lazy_attribute
    def uid(self):
        return str(uuid1())
    name = factory.Sequence(lambda n: 'Name #{}'.format(n))
    business_service = False
    technical_service = True
    pci_scope = False
    barcode = None
    object_id = True
    state = models_ci.CI_STATE_TYPES.INACTIVE.id
    status = models_ci.CI_STATUS_TYPES.REFERENCE.id
    type = factory.SubFactory(CITypeFactory)
    zabbix_id = None
    added_manually = False
    # TODO: add below fields:
    # content_object, content_type, layers, owners, relations


class ServiceCatalogFactory(CIFactory):
    FACTORY_FOR = models_device.ServiceCatalog
    FACTORY_DJANGO_GET_OR_CREATE = ('name', )
    state = models_ci.CI_STATE_TYPES.ACTIVE

    @factory.lazy_attribute
    def name(self):
        return service_name_generator.next()

    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(pk=models_ci.CI_TYPES.SERVICE.id)


class DeviceEnvironmentFactory(CIFactory):
    FACTORY_FOR = models_device.DeviceEnvironment
    state = models_ci.CI_STATE_TYPES.ACTIVE

    @factory.lazy_attribute
    def name(self):
        return env_name_generator.next()

    @factory.lazy_attribute
    def type(self):
        return models_ci.CIType.objects.get(
            pk=models_ci.CI_TYPES.ENVIRONMENT.id,
        )


class CIRelationFactory(DjangoModelFactory):
    FACTORY_FOR = models_ci.CIRelation

    parent = factory.SubFactory(ServiceCatalogFactory)
    child = factory.SubFactory(DeviceEnvironmentFactory)
    type = models_ci.CI_RELATION_TYPES.CONTAINS


class CIIncidentFactory(DjangoModelFactory):
    FACTORY_FOR = models_changes.CIIncident
    summary = factory.Sequence(lambda n: 'Summary: {}'.format(n))
    description = factory.Sequence(lambda n: 'Description: {}'.format(n))
    jira_id = factory.Sequence(lambda n: 'Jira ID: {}'.format(n))
    status = factory.Sequence(lambda n: 'Status: {}'.format(n))
    assignee = factory.Sequence(lambda n: 'Assignee: {}'.format(n))
    analysis = factory.Sequence(lambda n: 'Analysis: {}'.format(n))
    problems = factory.Sequence(lambda n: 'Problems: {}'.format(n))
    priority = factory.Sequence(lambda n: 'Priority: {}'.format(n))
    issue_type = None
    created_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    update_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    resolvet_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    planned_start_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    planned_end_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
