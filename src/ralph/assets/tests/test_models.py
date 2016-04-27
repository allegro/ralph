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

    def test_path_creation(self):
        self.assertEqual(
            self.conf_module_2.path,
            self.conf_module_1.path + '/' + self.conf_module_2.name
        )

    def test_update_module_children_path(self):
        self.conf_module_1.name = 'updated_name'
        self.conf_module_1.save()

        for conf in [
            self.conf_module_1, self.conf_module_2, self.conf_module_3,
            self.conf_class_1
        ]:
            conf.refresh_from_db()
            self.assertTrue(
                conf.path.startswith('updated_name'),
                msg='{} has not-updated path'.format(conf)
            )

    def test_update_class_path_update(self):
        self.conf_class_1.name = 'updated_name'
        self.conf_class_1.save()
        self.conf_class_1.refresh_from_db()
        self.assertTrue(self.conf_class_1.path.endswith('updated_name'))
