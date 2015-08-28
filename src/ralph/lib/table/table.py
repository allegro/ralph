try:
    from dj.choices import Choices
    use_choices = True
except ImportError:
    Choices = None
    use_choices = False

from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import flatatt

from ralph.admin.helpers import get_field_by_relation_path


class Table(object):

    """
    Generating contents for table based on predefined columns and queryset.

    Example:
        >>> table = Table(queryset, ['id', 'name'])
        >>> table.get_table_content()
        [
            ['id', 'name'],
            [
                {'value': '1', 'html_attributes': ''},
                {'value': 'Test', 'html_attributes': ''}
            ],
        ]
    """

    def __init__(self, queryset, list_display, additional_row_method=None):
        """
        Initialize table class

        :param queryset: django queryset
        :param list_display: field list to display
        :param additional_row_method: list of additional method for each row
        """
        self.queryset = queryset
        self.list_display = list_display
        self.additional_row_method = additional_row_method

    def get_headers(self):
        """
        Return headers for table.
        """
        headers = []
        for field in self.list_display:
            try:
                name = getattr(self, field).title
            except AttributeError:
                name = get_field_by_relation_path(
                    self.queryset.model, field
                ).verbose_name
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
                value = choice_class.name_from_id(item.get(field))
            else:
                value = item.get(field, None)
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
        if self.additional_row_method:
            colspan = len(self.list_display)
        for item in self.queryset.values(*list_display):
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
