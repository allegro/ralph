# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.assets.models.assets import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.choices import ObjectModelType


class CategoryFactory(DjangoModelFactory):

    class Meta:
        model = Category


class ManufacturerFactory(DjangoModelFactory):

    name = factory.Iterator(['Dell', 'Apple', 'Samsung'])

    class Meta:
        model = Manufacturer
        django_get_or_create = ['name']


class BackOfficeAssetModelFactory(DjangoModelFactory):

    name = factory.Iterator(['3310', 'XD300S', 'Hero 3', 'Computer set'])
    type = ObjectModelType.back_office

    class Meta:
        model = AssetModel
        django_get_or_create = ['name']


class DataCenterAssetModelFactory(DjangoModelFactory):

    name = factory.Iterator(['DL360', 'DL380p', 'DL380', 'ML10', 'ML10 v21'])
    type = ObjectModelType.data_center

    class Meta:
        model = AssetModel
        django_get_or_create = ['name']


class EnvironmentFactory(DjangoModelFactory):

    name = factory.Iterator(['prod', 'dev', 'test'])

    class Meta:
        model = Environment
        django_get_or_create = ['name']


class ServiceFactory(DjangoModelFactory):

    name = factory.Iterator(['Backup systems', 'load_balancing', 'databases'])

    class Meta:
        model = Service
        django_get_or_create = ['name']


class ServiceEnvironmentFactory(DjangoModelFactory):

    service = factory.SubFactory(ServiceFactory)
    environment = factory.SubFactory(EnvironmentFactory)

    class Meta:
        model = ServiceEnvironment
