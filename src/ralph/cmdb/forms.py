#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from ajax_select import make_ajax_field
from south.management.commands import patch_for_test_db_setup

from ralph.cmdb import models
from ralph.cmdb.models_ci import CIOwnership, CIOwner
from ralph.ui.widgets import (ReadOnlyWidget, ReadOnlyMultipleChoiceWidget,
                              ReadOnlySelectWidget)
from ralph.cmdb.models import CILayer, CIType
from ralph.cmdb import models  as db


class CISearchForm(forms.Form):
    uid = forms.CharField(label = ' CI UID ', max_length=100)
    layer = forms.ModelChoiceField(label = 'Layer',
            queryset = CILayer.objects.all(),
            empty_label='----'
    )
    type = forms.ModelChoiceField(
           label = 'CI Type',
           queryset = CIType.objects.all(),
           empty_label='----',
    )
    top_level = forms.BooleanField(label = 'Top lev.')
    parent = forms.CharField(label='',
            widget=forms.HiddenInput()
    )

class CIChangeSearchForm(forms.Form):
    type = forms.ChoiceField(choices=[['', '------']] + db.CI_CHANGE_TYPES())
    priority = forms.ChoiceField(choices = [['', '------']] + db.CI_CHANGE_PRIORITY_TYPES() )
    uid = forms.CharField(label = 'CI name', max_length=100)

class CIReportsParamsForm(forms.Form):
    this_month = forms.BooleanField()
    #date_start = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}),
    #        label = 'Date start')
    #date_end = forms.DateField(widget=forms.TextInput(attrs={'class' : 'datepicker'}),
    #        label = 'Date end')
    kind = forms.CharField(label = '', widget=forms.HiddenInput())

class CIEditForm(forms.ModelForm):
    class Meta:
        model = models.CI
        widgets = {
            'id': ReadOnlyWidget,
            'uid' : ReadOnlyWidget,
        }
        fields = (
            'id',
            'uid',
            'name',
            'type',
            'state',
            'status',
            'layers',
            'pci_scope',
            'business_owners',
            'technical_owners',
        )

    icons={
    }
    layers = forms.ModelMultipleChoiceField( models.CILayer.objects.all(),
            widget = FilteredSelectMultiple("layers", False,
                attrs={'rows' : '10' }
            )
    )
    business_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget=FilteredSelectMultiple("owners", False, attrs={'rows': '10'})
    )
    technical_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget=FilteredSelectMultiple("owners", False, attrs={'rows': '10'})
    )

    def __init__(self, *args, **kwargs):
        super(CIEditForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
            if self.initial.get('uid', None):
                self.data['uid'] = self.initial['uid']
            if self.initial.get('id', None):
                self.data['id'] = self.initial['id']
            if self.initial.get('name', None):
                self.data['name'] = self.initial['name']
        if len(self.initial):
            technical_owners, bussines_owners = [], []
            owns = CIOwnership.objects.filter(ci_id=self.initial.get('ci').id)
            for own in owns:
                if own.type == 1:
                    try:
                        technical_owners.append(CIOwner.objects.get(pk=str(own.owner_id)))
                    except CIOwner.DoesNotExist:
                        pass
                elif own.type == 2:
                    try:
                        bussines_owners.append(CIOwner.objects.get(pk=str(own.owner_id)))
                    except CIOwner.DoesNotExist:
                        pass
            self['technical_owners'].field.initial = technical_owners
            self['business_owners'].field.initial = bussines_owners


class CIViewForm(CIEditForm):
    class Meta:
        model = models.CI
        widgets = {
            'id': ReadOnlyWidget,
            'uid' : ReadOnlyWidget,
            'name' : ReadOnlyWidget,
            'type' : ReadOnlySelectWidget,
            'state' : ReadOnlySelectWidget,
            'status' : ReadOnlySelectWidget,
            'barcode' : ReadOnlyWidget,
            'pci_scope' : ReadOnlyWidget,

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
            widget = ReadOnlyMultipleChoiceWidget("layers", False,
                attrs={'rows' : '10' })
    )
    technical_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget = ReadOnlyMultipleChoiceWidget("owners", False,
                                              attrs={'rows' : '10' })
    )
    business_owners = forms.ModelMultipleChoiceField(
        models.CIOwner.objects.all().order_by('last_name', 'first_name'),
        widget = ReadOnlyMultipleChoiceWidget("owners", False,
                                              attrs={'rows' : '10' })
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

    icons={
    }
    parent = make_ajax_field(models.CIRelation, 'parent', 'ci', help_text=None)
    child = make_ajax_field(models.CIRelation, 'child', 'ci', help_text=None)

    def __init__(self, *args, **kwargs):
        super(CIRelationEditForm, self).__init__(*args, **kwargs)
        if self.data:
            self.data = self.data.copy()
