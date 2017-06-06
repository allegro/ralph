from unittest.mock import patch

from ddt import data, ddt, unpack

from ralph.assets.signals import custom_field_change
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.tests.factories import (
    ClusterFactory,
    DataCenterAssetFactory
)
from ralph.lib.custom_fields.models import (
    CustomField,
    CustomFieldTypes,
    CustomFieldValue
)
from ralph.tests import RalphTestCase
from ralph.virtual.tests.factories import CloudHostFactory, VirtualServerFactory


@ddt
class TestCustomFieldChangeHandler(RalphTestCase):
    def setUp(self):
        self.custom_field_str = CustomField.objects.create(
            name='test str', type=CustomFieldTypes.STRING, default_value='xyz'
        )

    @unpack
    @data(
        (CloudHostFactory,),
        (ClusterFactory,),
        (DataCenterAssetFactory,),
        (VirtualServerFactory,)
    )
    def test_should_publish_host_update_event_when_dc_host(self, m_factory):
        m_instance = m_factory()
        cfv = CustomFieldValue.objects.create(
            object=m_instance,
            custom_field=self.custom_field_str,
            value='sample_value'
        )
        with patch('ralph.assets.signals.publish_host_update') as mock:
            custom_field_change(
                sender=m_instance.__class__, instance=cfv
            )
            mock.assert_called_once_with(m_instance)

    def test_should_not_publish_host_update_event_when_not_dc_host(self):
        bo_asset = BackOfficeAssetFactory()
        cfv = CustomFieldValue.objects.create(
            object=bo_asset,
            custom_field=self.custom_field_str,
            value='sample_value'
        )
        with patch('ralph.assets.signals.publish_host_update') as mock:
            custom_field_change(
                sender=bo_asset.__class__, instance=cfv
            )
            self.assertFalse(mock.called)
