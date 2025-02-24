# -*- coding: utf-8 -*-
import re

from django import forms
from django.forms import ValidationError
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


class MultilineField(forms.CharField):
    """
    This field is a textarea which treats its content as many values seperated
    by `separators`
    Validation:
        - separated values cannot duplicate each other,
    """

    widget = forms.Textarea
    separators = r",|\n|\|"

    def __init__(self, allow_duplicates=True, *args, **kwargs):
        self.allow_duplicates = allow_duplicates
        super().__init__(*args, **kwargs)

    def validate(self, values):
        if not values and self.required:
            error_msg = _(
                "Field can't be empty. Please put the item OR items separated "
                "by new line or comma."
            )
            raise forms.ValidationError(error_msg, code="required")
        non_empty_values = [item for item in values if str(item).strip()]
        if not self.allow_duplicates:
            has_duplicates = len(set(non_empty_values)) != len(non_empty_values)
            if has_duplicates:
                raise forms.ValidationError(_("There are duplicates in field."))

    def to_python(self, value):
        items = []
        if value:
            for item in re.split(self.separators, value):
                items.append(item.strip(" \t\n\r"))

        return items


class IntegerMultilineField(MultilineField):
    def to_python(self, value):
        result = super().to_python(value)
        try:
            return [int(i) for i in result]
        except ValueError:
            raise ValidationError(_("Enter a valid number."))


class MultivalueFormMixin(object):
    """A form that has several multiline fields that need to have the
    same number of entries.

    :param multivalue_fields: list of form fields which require the same item
    count
    :param one_of_mulitvalue_required: list of form fields names which must
    be provided to form, e.g.
        one_of_mulitvalue_required = ['sn', 'barcode']
        means that if user inputs such data:
        sn, barcode:
        1,1, # valid
        2,   # valid
        ,2   # valid
        ,    # invalid, because neither sn nor barcode was provided
    """

    multivalue_fields = []
    one_of_mulitvalue_required = []
    model = None

    def equal_count_validator(self, cleaned_data):
        """Adds a validation error if form's multivalues fields have
        different count of items."""
        items_count_per_multi = set()
        for field in self.multivalue_fields:
            if cleaned_data.get(field, []):
                items_count_per_multi.add(len(cleaned_data.get(field, [])))
        if len(items_count_per_multi) > 1:
            for field in self.multivalue_fields:
                if field in cleaned_data:
                    msg = _(
                        ("Fields: %(fields)s " "- require the same number of items")
                    ) % {"fields": ", ".join(self.multivalue_fields)}
                    self.errors.setdefault(field, []).append(msg)

    def any_in_multivalues_validator(self, data):
        """
        Checks if each row has filled at least one field specified
        by one_of_mulitvalue_required.
        """

        def rows_of_required():
            rows_of_required = [
                self.cleaned_data[field_name]
                for field_name in self.one_of_mulitvalue_required
                if field_name in self.cleaned_data
            ]
            for multivalues_row in zip(*rows_of_required):
                yield multivalues_row

        if self.one_of_mulitvalue_required:
            for row_of_required in rows_of_required():
                if not any(row_of_required):
                    for field_name in self.one_of_mulitvalue_required:
                        errors = self._errors.setdefault(field_name, ErrorList())
                        msg = _("Fill at least on of %(v)s in each row") % {
                            "v": ",".join(self.one_of_mulitvalue_required)
                        }
                        errors.append(_(msg))
                    break

    def check_field_uniqueness(self, model, field_name, values):
        """
        Check field (pointed by *self.db_field_path*) uniqueness.
        If duplicated value is found then raise ValidationError

        :param string Model: model field to be unique (as a string)
        :param list values: list of field values
        """
        if not values:
            return
        conditions = {"{}__in".format(field_name): values}
        objs = model.objects.filter(**conditions)
        if objs:
            if hasattr(model, "get_absolute_url"):
                url = '<a href="{}">{}</a>'
                comma_items = ", ".join(
                    [url.format(obj.get_absolute_url(), obj.id) for obj in objs]
                )
            else:
                comma_items = ", ".join([str(obj) for obj in objs])
            msg = _("Following items already exist: ") + comma_items
            raise ValidationError(mark_safe(msg))

    def check_uniqness(self, data):
        for field_name in self.multivalue_fields:
            field = self[field_name].field
            if field.allow_duplicates:
                continue
            try:
                self.check_field_uniqueness(
                    self.model, field_name, data.get(field_name, [])
                )
            except forms.ValidationError as error:
                self._errors.setdefault(field_name, [])
                self._errors[field_name] += error.messages

    def extend_empty_fields_at_the_end(self, data):
        """
        Extend every field to have the same number of items. Additionaly remove
        empty rows from the end.
        """
        max_length = 0
        for field in self.multivalue_fields:
            value = data.get(field, [])
            max_length = max(max_length, len(value))
        for field in self.multivalue_fields:
            value = data.get(field, [])
            data[field] = value + [""] * (max_length - len(value))  # None?
        # remove empty lines
        while True:
            rows = list(zip(*[data[f] for f in self.multivalue_fields]))
            if len(rows) == 0:
                break
            if not any(rows[-1]):
                for field in self.multivalue_fields:
                    data[field].pop()
            else:
                break
        return data

    def clean(self):
        data = super().clean()
        self.extend_empty_fields_at_the_end(data)
        self.equal_count_validator(data)
        self.any_in_multivalues_validator(data)
        self.check_uniqness(data)
        return data
