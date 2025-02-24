# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from ralph.admin.widgets import PermissionsSelectWidget


class PerimissionsSelectWidgetTest(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.separator = " | "
        self.choices = (
            (1, self.separator.join(["app", "model", "can view model"])),
            (2, self.separator.join(["app", "model", "can change model"])),
            (3, self.separator.join(["app", "model", "can delete model"])),
        )
        self.widget = PermissionsSelectWidget(choices=self.choices)

    def test_render(self):
        """Test render items."""
        rendered_widget = self.widget.render(name="test_perms", value="")
        for value, label in self.choices:
            self.assertTrue(label.split(self.separator)[-1] in rendered_widget)

    def test_render_selected_option(self):
        """Test selected option."""
        rendered_option = self.widget.render_option([1, 2, 3], 1, "test")
        self.assertTrue("checked" in rendered_option)

    def test_get_value_from_dict(self):
        """Test get value from dictionary."""
        name = "test_perms"
        value = self.widget.value_from_datadict(
            data={name: "1,2,3"}, files=None, name=name
        )
        self.assertEqual(value, [1, 2, 3])
