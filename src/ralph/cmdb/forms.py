#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectField

from bob.forms.dependency import Dependency, DependencyForm, SHOW
from bob.forms.dependency_conditions import MemberOf as MemberOfCondition
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext_lazy as _

from ralph.cmdb import models
from ralph.cmdb import models as db
from ralph.cmdb.models import CIType
from ralph.cmdb.models_ci import (
    CIAttribute, CI_ATTRIBUTE_TYPES, CIAttributeValue,
)
from ralph.ui.widgets import (
    ReadOnlyWidget,
    ReadOnlyMultipleChoiceWidget,
    ReadOnlySelectWidget
)
from ralph.ui.widgets import DateWidget


class CISearchForm(forms.Form):
    uid = forms.CharField(label='CI name or UID', max_length=100)
    type = forms.ModelChoiceField(
        label='CI Type',
        queryset=CIType.objects.all(),
        empty_label='----',
    )
    top_level = forms.BooleanField(label=_('Top lev.'))
    show_inactive = forms.BooleanField(label=_('Show inact.'))
    parent = forms.CharField(
        label='', widget=forms.HiddenInput()
    )


class CIChangeSearchForm(forms.Form):
    type = forms.ChoiceField(choices=[['', '------']] + db.CI_CHANGE_TYPES())
    priority = forms.ChoiceField(
        choices=[['', '------']] + db.CI_CHANGE_PRIORITY_TYPES())
    uid = forms.CharField(label='CI name or uid', max_length=100)


class CIReportsParamsForm(forms.Form):
    this_month = forms.BooleanField()
    kind = forms.CharField(label='', widget=forms.HiddenInput())


class CIEditForm(DependencyForm, forms.ModelForm):

    CUSTOM_ATTRIBUTE_FIELDS = {
        CI_ATTRIBUTE_TYPES.INTEGER.id: forms.IntegerField,
        CI_ATTRIBUTE_TYPES.STRING.id: forms.CharField,
        CI_ATTRIBUTE_TYPES.DATE.id: forms.DateField,
        CI_ATTRIBUTE_TYPES.FLOAT.id: forms.FloatField,
        CI_ATTRIBUTE_TYPES.CHOICE.id: forms.ChoiceField,
    }

    class Meta:
        model = models.CI
        fields = (
            'name',
            'type',
            'state',
            'status',
            'layers',
            'pci_scope',
            'business_owners',
            'technical_owners',
        )

    icons = {
    }

    layers = forms.ModelMultipleChoiceField(
        models.CILayer.objects.all(),
        widget=FilteredSelectMultiple(
            "layers", False, attrs={'rows': '10'}
        )
    )
    business_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget=FilteredSelectMultiple("owners", False, attrs={'rows': '10'},),
        required=False
    )
    technical_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget=FilteredSelectMultiple("owners", False, attrs={'rows': '10'}),
        required=False
    )

    def _get_custom_attribute_field_name(self, attribute):
        """Returns the HTML field name for given attribute."""
        return 'attribute_{0}'.format(attribute.id)

    def _add_customattribute_fields(self):
        self.dependencies = self.dependencies or []
        for attribute in CIAttribute.objects.filter(
            ci_types=self.initial.get('type')
        ):
            field_name = self._get_custom_attribute_field_name(attribute)
            FieldType = self.CUSTOM_ATTRIBUTE_FIELDS[attribute.attribute_type]
            kwargs = {
                'label': attribute.name,
                'required': False,
            }
            if attribute.attribute_type == CI_ATTRIBUTE_TYPES.CHOICE:
                kwargs['choices'] = [
                    (x.split('.')[0], x.split('.')[-1])
                    for x in attribute.choices.split('|')
                ]
            self.fields[field_name] = FieldType(**kwargs)

            def add_prefix(field_name):
                return "%s-%s" % (
                    self.prefix, field_name
                ) if self.prefix else field_name

            self.dependencies.append(Dependency(
                add_prefix(field_name),
                add_prefix('type'),
                MemberOfCondition(list(attribute.ci_types.all())),
                SHOW,
            ))

    def __init__(self, *args, **kwargs):
        super(CIEditForm, self).__init__(*args, **kwargs)
        self._add_customattribute_fields()
        if len(self.initial):
            self['technical_owners'].field.initial =\
                self.instance.technical_owners.all()
            self['business_owners'].field.initial =\
                self.instance.business_owners.all()
            attribute_values = CIAttributeValue.objects.filter(
                ci=self.instance,
            )
            attribute_values = dict(
                ((av.attribute.name, av) for av in attribute_values)
            )
            for attribute in CIAttribute.objects.filter(
                ci_types=self.initial.get('type')
            ):
                attribute_value = attribute_values.get(attribute.name)
                if attribute_value is not None:
                    field_name = self._get_custom_attribute_field_name(
                        attribute,
                    )
                    self[field_name].field.initial = attribute_value.value

    def save(self, *args, **kwargs):
        instance = super(CIEditForm, self).save(*args, **kwargs)
        instance.owners.clear()
        instance.business_owners = self.cleaned_data['business_owners']
        instance.technical_owners = self.cleaned_data['technical_owners']

        for attribute in CIAttribute.objects.all():
            attribute_name = self._get_custom_attribute_field_name(attribute)
            value = self.cleaned_data.get(attribute_name)
            if value:
                CIAttributeValue.objects.filter(
                    ci=instance,
                    attribute=attribute,
                ).delete()
                attribute_value = CIAttributeValue(
                    ci=instance,
                    attribute=attribute,
                )
                attribute_value.save()
                attribute_value.value = value
        return instance


class CIViewForm(CIEditForm):

    class Meta:
        model = models.CI
        widgets = {
            'id': ReadOnlyWidget,
            'uid': ReadOnlyWidget,
            'name': ReadOnlyWidget,
            'type': ReadOnlySelectWidget,
            'state': ReadOnlySelectWidget,
            'status': ReadOnlySelectWidget,
            'barcode': ReadOnlyWidget,
            'pci_scope': ReadOnlyWidget,
        }
        fields = (
            'id',
            'uid',
            'name',
            'type',
            'state',
            'status',
            'layers',
            'barcode',
            'pci_scope',
        )
    layers = forms.ModelMultipleChoiceField(
        models.CILayer.objects.all(),
        widget=ReadOnlyMultipleChoiceWidget(
            "layers", False, attrs={'rows': '10'})
    )
    technical_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget=ReadOnlyMultipleChoiceWidget(
            "owners", False, attrs={'rows': '10'}),
        required=False
    )
    business_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget=ReadOnlyMultipleChoiceWidget(
            "owners", False, attrs={'rows': '10'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(CIViewForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            self.data['technical_owner'] = self.initial['technical_owner']


class CIRelationEditForm(forms.ModelForm):

    class Meta:
        model = models.CIRelation
        fields = (
            'id',
            'parent',
            'child',
            'type',
        )

    icons = {
    }

    parent = make_ajax_field(
        models.CIRelation,
        'parent',
        ('ralph.cmdb.models', 'CILookup'),
        help_text=None,
        required=True,
    )
    child = make_ajax_field(
        models.CIRelation,
        'child',
        ('ralph.cmdb.models', 'CILookup'),
        help_text=None,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super(CIRelationEditForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()


class SearchImpactForm(forms.Form):
    ci = AutoCompleteSelectField(
        ('ralph.cmdb.models', 'CILookup'),
        required=True,
        plugin_options={'minLength': 2}
    )


class ReportFilters(forms.Form):
    input_attrs = {'class': 'input-small'}

    ci = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs=dict(input_attrs, placeholder='ralph'),
        )
    )
    assignee = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs=dict(input_attrs, placeholder='John.'),
        )
    )
    jira_id = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs=dict(input_attrs, placeholder='TICKET-NUMBER'),
        )
    )
    issue_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', '----'),
            ('Bug', 'Bug'),
            ('Change-EM', 'Change-EM'),
            ('Change-OP', 'Change-OP'),
            ('Change-PL', 'Change-PL'),
            ('Improvement', 'Improvement'),
            ('Incident', 'Incident'),
            ('Incident-Security', 'Incident-Security'),
            ('New Feature', 'New Feature'),
            ('Problem', 'Problem'),
            ('Project Info', 'Project Info'),
            ('SR-Permission', 'SR-Permission'),
            ('Service Request', 'Service Request'),
            ('Task', 'Task'),
        ],
        label='Issue type',
        widget=forms.Select(
            attrs=input_attrs,
        )
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', '----'),
            ('Open', 'Open'),
            ('In Progress', 'In Progress'),
            ('Reopened', 'Reopened'),
            ('Resolved', 'Resolved'),
            ('Closed', 'Closed'),
            ('Blocked', 'Blocked'),
            ('Todo', 'Todo'),
            ('In Test', 'In Test'),
            ('To Deploy', 'To Deploy'),
            ('In Deploy', 'In Deploy'),
            ('Accepted', 'Accepted'),
        ],
        label='Issue status',
        widget=forms.Select(
            attrs=input_attrs,
        )
    )


class ReportFiltersDateRange(forms.Form):
    date_attrs = {
        'data-collapsed': True,
        'class': 'input-small',
    }
    start_update = forms.DateField(
        required=False,
        widget=DateWidget(dict(
            date_attrs,
            placeholder='From',
        )),
        label="Update"
    )
    end_update = forms.DateField(
        required=False,
        widget=DateWidget(
            attrs={
                'placeholder': 'End',
                'data-collapsed': True,
                'class': 'input-small',
            }
        ),
        label="",
    )
    start_resolved = forms.DateField(
        required=False,
        widget=DateWidget(dict(date_attrs, placeholder='From')),
        label="Resolved",
    )
    end_resolved = forms.DateField(
        required=False,
        widget=DateWidget(dict(date_attrs, placeholder='To')),
        label="",
    )
    start_planned_start = forms.DateField(
        required=False,
        widget=DateWidget(dict(date_attrs, placeholder='From')),
        label="Planed start",
    )
    end_planned_start = forms.DateField(
        required=False,
        widget=DateWidget(dict(date_attrs, placeholder='To')),
        label="",
    )
    start_planned_end = forms.DateField(
        required=False,
        widget=DateWidget(dict(date_attrs, placeholder='From')),
        label="Planed end",
    )
    end_planned_end = forms.DateField(
        required=False,
        widget=DateWidget(dict(date_attrs, placeholder='To')),
        label="",
    )
