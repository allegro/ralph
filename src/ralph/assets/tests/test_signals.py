from unittest.mock import patch

from ddt import data, ddt, unpack
from django.test import TransactionTestCase

from ralph.assets.models import ConfigurationClass, Ethernet
from ralph.assets.signals import custom_field_change
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.tests.factories import (
    ClusterFactory,
    ConfigurationClassFactory,
    DataCenterAssetFactory
)
from ralph.lib.custom_fields.models import (
    CustomField,
    CustomFieldTypes,
    CustomFieldValue
)
from ralph.networks.models import IPAddress
from ralph.tests import RalphTestCase
from ralph.virtual.tests.factories import CloudHostFactory, VirtualServerFactory


@ddt
class TestCustomFieldChangeHandler(RalphTestCase):
    def setUp(self):
        self.custom_field_str = CustomField.objects.create(
            name="test str", type=CustomFieldTypes.STRING, default_value="xyz"
        )

    @unpack
    @data(
        (CloudHostFactory,),
        (ClusterFactory,),
        (DataCenterAssetFactory,),
        (VirtualServerFactory,),
    )
    def test_should_publish_host_update_event_when_dc_host(self, m_factory):
        m_instance = m_factory()
        cfv = CustomFieldValue.objects.create(
            object=m_instance, custom_field=self.custom_field_str, value="sample_value"
        )
        with patch("ralph.assets.signals.publish_host_update") as mock:
            custom_field_change(sender=m_instance.__class__, instance=cfv)
            mock.assert_called_once_with(m_instance)

    def test_should_not_publish_host_update_event_when_not_dc_host(self):
        bo_asset = BackOfficeAssetFactory()
        cfv = CustomFieldValue.objects.create(
            object=bo_asset, custom_field=self.custom_field_str, value="sample_value"
        )
        with patch("ralph.assets.signals.publish_host_update") as mock:
            custom_field_change(sender=bo_asset.__class__, instance=cfv)
            self.assertFalse(mock.called)


@ddt
class TestRelatedObjectsChangeHandler(TransactionTestCase):
    @unpack
    @data(
        (CloudHostFactory,),
        (ClusterFactory,),
        (DataCenterAssetFactory,),
        (VirtualServerFactory,),
    )
    def test_should_publish_host_update_when_ipaddress_added(self, model_factory):
        model_instance = model_factory()
        with patch("ralph.data_center.publishers.publish_host_update") as mock:
            IPAddress.objects.create(address="10.20.30.40", base_object=model_instance)
            # will be called 2 times: for Ethernet and for IPAddress
            mock.assert_called_with(model_instance)

    @unpack
    @data(
        (CloudHostFactory,),
        (ClusterFactory,),
        (DataCenterAssetFactory,),
        (VirtualServerFactory,),
    )
    def test_should_publish_host_update_when_ethernet_added(self, model_factory):
        model_instance = model_factory()
        with patch("ralph.data_center.publishers.publish_host_update") as mock:
            Ethernet.objects.create(mac="aa:bb:cc:dd:ee:ff", base_object=model_instance)
            mock.assert_called_once_with(model_instance)

    @unpack
    @data(
        (CloudHostFactory,),
        (ClusterFactory,),
        (DataCenterAssetFactory,),
        (VirtualServerFactory,),
    )
    def test_should_publish_host_update_when_conf_class_changed(self, model_factory):
        conf_class = ConfigurationClassFactory()
        model_factory.create_batch(2, configuration_path=conf_class)
        with patch("ralph.data_center.publishers.publish_host_update") as mock:
            # refresh instance to not fall into post_commit single event
            conf_class = ConfigurationClass.objects.get(pk=conf_class.pk)
            conf_class.name = "another_class"
            conf_class.save()
            self.assertEqual(mock.call_count, 2)

    @unpack
    @data(
        (CloudHostFactory,),
        (ClusterFactory,),
        (DataCenterAssetFactory,),
        (VirtualServerFactory,),
    )
    def test_should_publish_host_update_when_conf_module_changed(self, model_factory):
        conf_class = ConfigurationClassFactory()
        model_factory.create_batch(2, configuration_path=conf_class)
        with patch("ralph.data_center.publishers.publish_host_update") as mock:
            conf_class.module.name = "another_module"
            conf_class.module.save()
            self.assertEqual(mock.call_count, 2)
