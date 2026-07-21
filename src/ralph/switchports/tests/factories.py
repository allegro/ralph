from factory import SubFactory, post_generation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from ralph.data_center.tests.factories import DataCenterAssetFactory, RackFactory
from ralph.switchports.models import (
    Port,
    Connection,
    ConnectionMember,
    RackSwitchConfigurationOverride,
    RackSwitchConfiguration,
    RackConfiguration,
)


class PortFactory(DjangoModelFactory):
    class Meta:
        model = Port

    label = "0/0/0"
    data_center_asset = SubFactory(DataCenterAssetFactory)


class ConnectionFactory(DjangoModelFactory):
    class Meta:
        model = Connection

    @post_generation
    def post_members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted is not None:
            for port in extracted:
                ConnectionMember(connection=self, port=port).save()
        else:
            for _ in range(2):
                ConnectionMember(connection=self, port=PortFactory()).save()


class RackConfigurationFactory(DjangoModelFactory):
    class Meta:
        model = RackConfiguration

    rack = SubFactory(RackFactory)
    description = FuzzyText()


class RackSwitchConfigurationFactory(DjangoModelFactory):
    class Meta:
        model = RackSwitchConfiguration

    rack_configuration = SubFactory(RackConfigurationFactory)
    switch = SubFactory(DataCenterAssetFactory)
    label = 'eth1'
    backend_validation = False


class RackSwitchConfigurationOverrideFactory(DjangoModelFactory):
    class Meta:
        model = RackSwitchConfigurationOverride

    data_center_asset = SubFactory(DataCenterAssetFactory)
    rack_switch_configuration = SubFactory(RackSwitchConfigurationFactory)
    switch = SubFactory(DataCenterAssetFactory)
