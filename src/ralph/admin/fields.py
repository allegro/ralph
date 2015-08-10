# -*- coding: utf-8 -*-
import copy
import re

from django import forms
from django.contrib import messages
from django.db import transaction
from django.forms.models import save_instance
from django.forms.util import ErrorList
from django.utils.translation import ugettext as _


class MultilineField(forms.CharField):
    """
    This field is a textarea which treats its content as many values seperated
    by `separators`
    Validation:
        - separated values cannot duplicate each other,
    """
    widget = forms.Textarea
    separators = ",|\n"

    def __init__(self, allow_duplicates=True, *args, **kwargs):
        self.allow_duplicates = allow_duplicates
        super().__init__(*args, **kwargs)

    def validate(self, values):
        if not values and self.required:
            error_msg = _(
                "Field can't be empty. Please put the item OR items separated "
                "by new line or comma."
            )
            raise forms.ValidationError(error_msg, code='required')
        if not self.allow_duplicates:
            # check if duplicates
            has_duplicates = len(set(values)) != len(values)
            if has_duplicates:
                raise forms.ValidationError(_("There are duplicates in field."))

    def to_python(self, value):
        items = []
        if value:
            for item in re.split(self.separators, value):
                items.append(item.strip())
        return items


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
        ,    # invalid, because `sn` neither `barcode` was provided
    """
    multivalue_fields = []
    one_of_mulitvalue_required = []

    def save(self, commit=True):
        if self.instance.id:
            obj = super().save(commit)
        else:
            obj = self.bulk_add(commit)
        return obj

    @transaction.atomic
    def bulk_add(self, commit):
        objs = []
        fail_message = _('Unable to add assets')
        for row_as_dict in self.multivalue_rows_as_dict():
            obj_data = copy.deepcopy(self.cleaned_data)
            obj_data.update(row_as_dict)
            obj = self._meta.model(**obj_data)
            save_instance(
                self, obj, self._meta.fields, fail_message, commit,
                self._meta.exclude, construct=False
            )
            objs.append(obj)
        if len(objs) > 1:
            obj_name = self._meta.model._meta.verbose_name_plural
        else:
            obj_name = self._meta.model._meta.verbose_name
        msg = _(
            'Successfully added {} {}'.format(len(objs), str(obj_name)),
        )
        if hasattr(self, '_request'):
            messages.info(self._request, msg)
        return objs[0]

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
                    msg = "Fields: {} - require the same count".format(
                        ', '.join(self.multivalue_fields)
                    )
                    self.errors.setdefault(field, []).append(msg)

    def multivalue_rows_as_dict(self):
        for key in self.multivalue_fields:
            if key in self.cleaned_data:
                any_row = self.cleaned_data[key]
                break
        else:
            return []

        for idx, null in enumerate(any_row):
            row = {}
            for key in self.multivalue_fields:
                if key in self.cleaned_data:
                    row[key] = self.cleaned_data[key][idx]
            yield row

    def any_in_multivalues_validator(self, data):
        def rows_of_required():
            rows_of_required = [
                self.cleaned_data[field_name] for field_name in
                self.one_of_mulitvalue_required if field_name in
                self.cleaned_data
            ]
            for multivalues_row in zip(*rows_of_required):
                yield multivalues_row

        if self.one_of_mulitvalue_required:
            for row_of_required in rows_of_required():
                if not any(row_of_required):
                    for field_name in self.one_of_mulitvalue_required:
                        errors = self._errors.setdefault(
                            field_name, ErrorList()
                        )
                        msg = 'Fill at least on of {} in each row'.format(
                            ','.join(self.one_of_mulitvalue_required)
                        )
                        errors.append(_(msg))

    def clean(self):
        data = super().clean()
        self.equal_count_validator(data)
        self.any_in_multivalues_validator(data)
        return data
