try:
    from dj.choices import Choices
    use_choices = True
except ImportError:
    Choices = None
    use_choices = False

from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import flatatt

from ralph.admin.helpers import (
    get_field_by_relation_path,
    get_field_title_by_relation_path,
    getattr_dunder
)


class Table(object):

    """
    Generating contents for table based on predefined columns and queryset.

    Example:
        >>> table = Table(queryset, ['id', 'name'])
        >>> table.get_table_content()
        [
            ['id', ('name', 'My field name')],
            [
                {'value': '1', 'html_attributes': ''},
                {'value': 'Test', 'html_attributes': ''}
            ],
        ]
    """

    def __init__(
        self, queryset, list_display, additional_row_method=None, request=None
    ):
        """
        Initialize table class

        Args:
            queryset: django queryset
            list_display: field list to display
            additional_row_method: list of additional method for each row
        """
        self.queryset = queryset
        self.list_display_raw = list_display
        self.list_display = [
            (f[0] if isinstance(f, (tuple, list)) else f) for f in list_display
        ]
        self.additional_row_method = additional_row_method
        self.request = request

    def get_headers(self):
        """
        Return headers for table.
        """
        headers = []
        for field in self.list_display_raw:
            if isinstance(field, (list, tuple)):
                headers.append(field[1])
            else:
                try:
                    name = getattr(self, field).title
                except AttributeError:
                    name = get_field_title_by_relation_path(
                        self.queryset.model, field
                    )
                headers.append(name)
        return headers

    def get_field_value(self, item, field):
        """
        Returns the value for the given field name.

        Looking in:
             If the field is type Choices returns choice name
             else returns the value of row

        :param item: row from dict
        :param field: field name
        """
        value = None
        if hasattr(self, field):
            value = getattr(self, field)(item)
        else:
            value = getattr_dunder(item, field)
            try:
                choice_class = get_field_by_relation_path(
                    self.queryset.model, field
                ).choices
            except FieldDoesNotExist:
                choice_class = None
            if (
                use_choices and choice_class and
                isinstance(choice_class, Choices)
            ):
                value = choice_class.name_from_id(value)
        return value

    def get_table_content(self):
        """
        Return content of table.
        """
        result = [self.get_headers()]
        # Remove fields which are not in model
        list_display = [
            field for field in self.list_display if not hasattr(self, field)
        ]
        if 'id' not in list_display:
            list_display.append('id')
        if self.additional_row_method:
            colspan = len(self.list_display)

        for item in self.queryset:
            result.append([
                {
                    'value': self.get_field_value(item, field),
                    'html_attributes': ''
                } for field in self.list_display
            ])
            if self.additional_row_method:
                for method in self.additional_row_method:
                    additional_data = [
                        {'value': i, 'html_attributes': flatatt(
                            {'colspan': colspan}
                        )} for i in getattr(self, method)(item)
                    ]
                    if additional_data:
                        result.append(additional_data)
        return result
