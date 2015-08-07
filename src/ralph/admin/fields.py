# -*- coding: utf-8 -*-
import re

from django import forms
from django.db import transaction
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
        super(MultilineField, self).__init__(*args, **kwargs)

    def validate(self, values):
        if not values and self.required:
            error_msg = _(
                "Field can't be empty. Please put the item OR items separated "
                "by new line or comma."
            )
            raise forms.ValidationError(error_msg, code='required')
        if not self.allow_duplicates:
            # check if duplicates
            is_duplicates = len(set(values)) != len(values)
            if is_duplicates:
                raise forms.ValidationError(_("There are duplicates in field."))

    def to_python(self, value):
        items = []
        if value:
            for item in re.split(self.separators, value):
                items.append(item.strip())
        return items

    def clean(self, value):
        value = super(MultilineField, self).clean(value)
        return value


class MultivalueFormMixin(object):
    """A form that has several multiline fields that need to have the
    same number of entries.

    :param multivalue_fields: list of form fields which require the same item
    count
    """
    multivalue_fields = []
    one_of_mulitvalue_required = []

    @transaction.atomic
    def save(self, commit=True):
        import copy
        objs = []
        for row_as_dict in self.multivalues_rows_as_dict():
            obj_data = copy.deepcopy(self.cleaned_data)
            #import ipdb;ipdb.set_trace()
            obj_data.update(row_as_dict)
            obj = self._meta.model(**obj_data)
            #import ipdb;ipdb.set_trace()
            obj.save()
            objs.append(obj)
        if len(objs) > 1:
            obj_name = self._meta.model._meta.verbose_name_plural
        else:
            obj_name = self._meta.model._meta.verbose_name
        msg = _(
            'Successfully added {} {}'.format(
                len(objs), str(obj_name)
            ),
        )
        #self.message_user(request, msg)

        #obj = self.model(**form.cleaned_data)
        #for idx, form_values in enumerate(self.multivalues_rows()):
        #    for value, field_name in zip(form_values, self.multivalue_fields):
        #        setattr(obj, field_name, value)
        #msg = _('Successfully added {} assets'.format(idx + 1))
        #self.message_user(request, msg)

    def equal_count_validator(self, cleaned_data):
        """Adds a validation error if if form's multivalues fields have
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

    def multivalues_rows_as_dict(self):
        #TODO:: change name
        i = 0
        while True:
            row = {}
            print(i)
            for key in self.multivalue_fields:
                if key in self.cleaned_data:
                    try:
                        row[key] = self.cleaned_data[key][i]
                    except IndexError:
                        raise StopIteration
            yield row
            i += 1

        multivalues_rows = [
            self.cleaned_data[field_name]
            for field_name in self.multivalue_fields
            if field_name in self.cleaned_data
        ]
        for multivalues_row in zip(*multivalues_rows):
            yield multivalues_row

    def multivalues_rows(self):
        multivalues_rows = [
            self.cleaned_data[field_name] for field_name in
            self.one_of_mulitvalue_required if field_name in self.cleaned_data
        ]
        for multivalues_row in zip(*multivalues_rows):
            yield multivalues_row

    def any_in_multivalues_validator(self, data):
        if self.one_of_mulitvalue_required:
            for multivalues_row in self.multivalues_rows():
                if not any(multivalues_row):
                    for field_name in self.one_of_mulitvalue_required:
                        errors = self._errors.setdefault(
                            field_name, ErrorList()
                        )
                        msg = 'Fill at least on of {} in each row'.format(
                            ','.join(self.one_of_mulitvalue_required)
                        )
                        errors.append(_(msg))

    def clean(self):
        data = super(MultivalueFormMixin, self).clean()
        self.equal_count_validator(data)
        self.any_in_multivalues_validator(data)
        return data
