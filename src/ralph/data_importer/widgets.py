# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from import_export import widgets

from ralph.assets.models.assets import ServiceEnvironment
from ralph.data_center.models.physical import DataCenterAsset
from ralph.back_office.models import BackOfficeAsset


class AssetServiceEnvWidget(widgets.ForeignKeyWidget):

    """Widget for AssetServiceEnv Foreign Key field.

    CSV field format Service.name|Environment.name
    """

    def clean(self, value):
        try:
            value = value.split("|")  # service, enviroment
            value = ServiceEnvironment.objects.get(
                service__name=value[0],
                environment__name=value[1]
            )
        except ServiceEnvironment.DoesNotExist:
            value = None
        return value

    def render(self, value):
        if value is None:
            return ""
        return "{}|{}".format(
            value.service.name,
            value.environment.name
        )


class BaseObjectWidget(widgets.ForeignKeyWidget):

    """Widget for BaseObject Foreign Key field.

    CSV field format: DataCenterAsset.sn or BackOfficeAsset.sn
    """

    def clean(self, value):
        asset = DataCenterAsset.objects.filter(sn=value).first()
        if not asset:
            asset = BackOfficeAsset.objects.filter(sn=value).first()
        if asset:
            return asset.baseobject_ptr
        return None

    def render(self, value):
        if value is None:
            return ""
        return value.id
