#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
from django import forms
import ralph.cmdb.models  as db

def _get_pages(paginator, page):
    pages = paginator.page_range[max(0, page - 4):min(paginator.num_pages, page + 3)]
    if 1 not in pages:
        pages.insert(0, 1)
        pages.insert(1, '...')
    if paginator.num_pages not in pages:
        pages.append('...')
        pages.append(paginator.num_pages)
    return pages

class CustomFieldForm(forms.BaseForm):
    """
    Handle save action on dynamically built form
    """
    def save(self):
        data = self.cleaned_data
        matcher = re.compile("attribute_(\w+)_(\w+)")
        for i in data.keys():
            value = data[i]
            match = matcher.match(i)
            if match:
                field_id = int(match.groups()[1])
                field_type = match.groups()[0]
                attributes = db.CIAttributeValue.objects.filter(
                        ci=self.ci,
                        attribute_id=field_id
                )
                attributes.delete()
                init_params = dict()
                if field_type == 'string':
                    value = db.CIValueString(value=value)
                    init_params['value_string'] = value
                elif field_type == 'integer':
                    value = db.CIValueInteger(value=value)
                    init_params['value_integer'] = value
                elif field_type == 'date':
                    value = db.CIValueDate(value=value)
                    init_params['value_date'] = value
                elif field_type == 'float':
                    value = db.CIValueFloat(value=value)
                    init_params['value_float'] = value
                elif field_type == 'choice':
                    value = db.CIValueChoice(value=value)
                    init_params['value_choice'] = value
                else:
                    raise TypeError("Unknown type %s" % field_type)
                value.save()
                ci_attribute_value = db.CIAttributeValue(
                        ci=self.ci,
                        attribute_id = field_id,
                        **init_params
                )
                ci_attribute_value.save()
            else:
                raise TypeError("Can't lookup form field %s" % field_id)


class EditAttributeFormFactory(object):
    def __init__(self, ci):
        self.ci_type =ci.type
        self.ci_id = ci.id
        self.ci = ci
        self.fields = self.ci_attributes = db.CIAttribute.objects.filter(ci_types__id__contains=self.ci_type.id)

    def factory(self, *args, **kwargs):
        return self.make_attributes_form(self.fields)(*args, **kwargs)

    def make_attributes_form(self, fields):
        form_fields={}
        form_field = None
        field_type = None
        for field in fields:
            if field.attribute_type == db.CI_ATTRIBUTE_TYPES.INTEGER.id:
                 field_type = 'integer'
                 form_field = forms.IntegerField(
                required = False,
                 label = field.name )
            elif field.attribute_type == db.CI_ATTRIBUTE_TYPES.STRING.id:
                field_type = 'string'
                form_field = forms.CharField(
                required = False,
                label = field.name, max_length = 100)
            elif field.attribute_type == db.CI_ATTRIBUTE_TYPES.DATE.id:
                field_type = 'date'
                form_field = forms.DateField(
                required = False, label = field.name)
            elif field.attribute_type == db.CI_ATTRIBUTE_TYPES.FLOAT.id:
                field_type = 'float'
                form_field = forms.FloatField(
                required = False, label = field.name)
            elif field.attribute_type == db.CI_ATTRIBUTE_TYPES.CHOICE.id:
                field_type = 'choice'
                form_field = forms.ChoiceField(
                        choices = [(x.split('.')[0], x.split('.')[-1]) for x in field.choices.split('|')],
                required = False,
                label = field.name )
            #fixme - field_type do integera
            form_fields['attribute_%s_%s' % (field_type, field.id)] = form_field
        self.form = type(b'FieldForm', (CustomFieldForm, ), {
            b'base_fields': form_fields,
            b'icons' : {},
            })
        self.form.ci = self.ci
        return self.form

