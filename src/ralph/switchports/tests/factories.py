from factory import SubFactory, post_generation
from factory.django import DjangoModelFactory

from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.switchports.models import Port, Connection, ConnectionMember


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
