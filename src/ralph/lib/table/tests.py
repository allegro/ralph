from django.test import TestCase

from ralph.lib.table.table import Table
from ralph.tests.models import Foo


class TableRenderTestCase(TestCase):

    """TestCase for Table class."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.foo_1 = Foo.objects.create(bar='Test1')

    def assertTablesEqual(self, table1, table2):
        """
        Compare content of the rows (without checking row type (list vs tuple))
        """
        self.assertEqual(len(table1), len(table2))
        for row1, row2 in zip(table1, table2):
            self.assertSequenceEqual(row1, row2)

    def test_queryset_render(self):
        """Test get_perm_key function."""
        table = Table(Foo.objects.all(), ['id', 'bar'])
        result = [
            [{'value': 'ID'}, {'value': 'bar'}],
            [
                {'value': self.foo_1.id, 'html_attributes': ''},
                {'value': 'Test1', 'html_attributes': ''}
            ]
        ]
        self.assertTablesEqual(table.get_table_content(), result)

    def test_queryset_render_transposed(self):
        """Test get_perm_key function."""
        table = Table(Foo.objects.all(), ['id', 'bar'], transpose=True)
        result = [
            [{'value': 'ID'}, {'value': self.foo_1.id, 'html_attributes': ''}],
            [{'value': 'bar'}, {'value': 'Test1', 'html_attributes': ''}]
        ]
        self.assertTablesEqual(table.get_table_content(), result)

    def test_custom_field(self):
        class CustomTable(Table):
            def url(self, item):
                return 'custom_value'
            url.title = 'custom_title'

        table = CustomTable(Foo.objects.all(), ['id', 'bar', 'url'])
        result = [
            [{'value': 'ID'}, {'value': 'bar'}, {'value': 'custom_title'}],
            [
                {'value': self.foo_1.id, 'html_attributes': ''},
                {'value': 'Test1', 'html_attributes': ''},
                {'value': 'custom_value', 'html_attributes': ''}
            ]
        ]
        self.assertTablesEqual(table.get_table_content(), result)

    def test_additional_row_method(self):
        class CustomTable(Table):
            def bar_url(self, item):
                return ['custom_bar']
        table = CustomTable(Foo.objects.all(), ['id', 'bar'], ['bar_url'])
        result = [
            [{'value': 'ID'}, {'value': 'bar'}],
            [
                {'value': self.foo_1.id, 'html_attributes': ''},
                {'value': 'Test1', 'html_attributes': ''},
            ],
            [
                {'value': 'custom_bar', 'html_attributes': ' colspan="2"'}
            ]
        ]
        self.assertTablesEqual(table.get_table_content(), result)
