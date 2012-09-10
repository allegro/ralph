#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from ajax_select import make_ajax_field

from ralph.cmdb import models
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
        )

    icons={
    }
    layers = forms.ModelMultipleChoiceField( models.CILayer.objects.all(),
            widget = FilteredSelectMultiple("layers", False,
                attrs={'rows' : '10' }
            )
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
            'technical_owner' : ReadOnlyWidget,

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
            'technical_owner',
        )
    layers = forms.ModelMultipleChoiceField(
            models.CILayer.objects.all(),
            widget = ReadOnlyMultipleChoiceWidget("layers", False,
                attrs={'rows' : '10' })
    )
    technical_owner = forms.CharField(widget = ReadOnlyWidget())

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
