try:
    from dj.choices import Choices
    use_choices = True
except ImportError:
    Choices = None
    use_choices = False

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape

from ralph.admin.helpers import (
    get_field_by_relation_path,
    get_field_title_by_relation_path,
    getattr_dunder
)


class Table(object):
    """
    Generating contents for table based on predefined columns and queryset.

    Example:
        >>> table = Table(queryset, ['id', ('name', 'My field name')])
        >>> table.get_table_content()
        [
            [{'value': id'}, {'value': 'My field name'}],
            [
                {'value': '1', 'html_attributes': ''},
                {'value': 'Test', 'html_attributes': ''}
            ],
        ]

    See __init__'s docstring for additional info about Table params.
    """
    template_name = 'table.html'

    def __init__(
        self, queryset, list_display, additional_row_method=None, request=None,
        transpose=False,
    ):
        """
        Initialize table class

        Args:
            queryset: django queryset
            list_display: field list to display; a value on the list could be
                plain string (name of model's field - verbose name of field
                will be used here) or tuple (field_name, verbose_name)
            additional_row_method: list of additional method for each row
            transpose: set to True if table should be transposed (rows swapped
                with columns)
        """
        self.queryset = queryset
        self.list_display_raw = list_display
        self.list_display = [
            (f[0] if isinstance(f, (tuple, list)) else f) for f in list_display
        ]
        self.additional_row_method = additional_row_method
        self.request = request
        self.transpose = transpose

    @property
    def headers_count(self):
        return len(self.get_headers())

    @property
    def rows_count(self):
        return self.queryset.count()

    def get_headers(self):
        """
        Return headers for table.
        """
        headers = []
        for field in self.list_display_raw:
            if isinstance(field, (list, tuple)):
                headers.append({'value': field[1]})
            else:
                try:
                    name = getattr(self, field).title
                except AttributeError:
                    name = get_field_title_by_relation_path(
                        self.queryset.model, field
                    )
                headers.append({'value': name})
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
                    item._meta.model, field
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
        if self.transpose:
            result = list(zip(*result))
        return result

    def render(self, request=None):
        content = self.get_table_content()
        context = {
            'show_header': not self.transpose,
            'headers_count': self.headers_count,
            'rows_count': self.rows_count,
            'LIMIT': 5
        }
        if self.transpose:
            context.update({'rows': content})
        else:
            context.update({'headers': content[0], 'rows': content[1:]})
        return render_to_string(
            self.template_name,
            context=context,
            request=request,
        )


class TableWithUrl(Table):
    """
    Table with built-in url column.
    """

    def get_field_value(self, item, field):
        value = super().get_field_value(item, field)
        if field == self.url_field:
            return '<a href="{}">{}</a>'.format(
                reverse(
                    'admin:view_on_site',
                    args=(ContentType.objects.get_for_model(item).id, item.id,)
                ),
                escape(value)
            )
        return value

    def __init__(self, queryset, list_display, *args, **kwargs):
        self.url_field = kwargs.pop('url_field', None)
        super().__init__(
            queryset=queryset, list_display=list_display, *args, **kwargs
        )
