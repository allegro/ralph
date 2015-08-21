from django.test import TestCase

from ralph.lib.table import Table
from ralph.tests.models import Foo


class TableRenderTestCase(TestCase):

    """TestCase for Table class."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.foo_1 = Foo.objects.create(bar='Test1')

    def test_queryset_render(self):
        """Test get_perm_key function."""
        table = Table(Foo.objects.all(), ['id', 'bar'])
        result = [
            ['ID', 'bar'],
            [
                {'value': self.foo_1.id, 'html_attributes': ''},
                {'value': 'Test1', 'html_attributes': ''}
            ]
        ]
        self.assertListEqual(table.get_table_content(), result)

    def test_custom_field(self):
        class CustomTable(Table):
            def url(self, item):
                return 'custom_value'
            url.title = 'custom_title'

        table = CustomTable(Foo.objects.all(), ['id', 'bar', 'url'])
        result = [
            ['ID', 'bar', 'custom_title'],
            [
                {'value': self.foo_1.id, 'html_attributes': ''},
                {'value': 'Test1', 'html_attributes': ''},
                {'value': 'custom_value', 'html_attributes': ''}
            ]
        ]
        self.assertListEqual(table.get_table_content(), result)

    def test_additional_row_method(self):
        class CustomTable(Table):
            def bar_url(self, item):
                return ['custom_bar']
        table = CustomTable(Foo.objects.all(), ['id', 'bar'], ['bar_url'])
        result = [
            ['ID', 'bar'],
            [
                {'value': self.foo_1.id, 'html_attributes': ''},
                {'value': 'Test1', 'html_attributes': ''},
            ],
            [
                {'value': 'custom_bar', 'html_attributes': ' colspan="2"'}
            ]
        ]
        self.assertListEqual(table.get_table_content(), result)
