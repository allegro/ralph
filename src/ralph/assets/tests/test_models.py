# -*- coding: utf-8 -*-
from ralph.assets.tests.factories import (
    ConfigurationClassFactory,
    ConfigurationModuleFactory
)
from ralph.tests import RalphTestCase


class ConfigurationTest(RalphTestCase):
    def setUp(self):
        self.conf_module_1 = ConfigurationModuleFactory()
        self.conf_module_2 = ConfigurationModuleFactory(
            parent=self.conf_module_1
        )
        self.conf_module_3 = ConfigurationModuleFactory(
            parent=self.conf_module_2
        )
        self.conf_class_1 = ConfigurationClassFactory(
            module=self.conf_module_3
        )

    def test_update_module_children_path(self):
        self.conf_module_3.name = 'updated_name'
        self.conf_module_3.save()

        self.conf_class_1.refresh_from_db()
        self.assertTrue(
            self.conf_class_1.path.startswith('updated_name'),
        )

    def test_update_class_path_update(self):
        self.conf_class_1.class_name = 'updated_name'
        self.conf_class_1.save()
        self.conf_class_1.refresh_from_db()
        self.assertTrue(self.conf_class_1.path.endswith('updated_name'))
