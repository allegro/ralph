#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django import forms
from django.contrib import admin
from lck.django.common.admin import ModelAdmin

from ajax_select.fields import AutoCompleteSelectField

import ralph.cmdb.models as db
from ralph.cmdb.models_changes import CIChangeGit
from ralph.ui.widgets import ReadOnlyPreWidget


class GitPathMappingAdminForm(forms.ModelForm):
    class Meta:
        model = db.GitPathMapping

    ci = AutoCompleteSelectField('ci')
    occurences = forms.CharField(
        required=False,
        widget=ReadOnlyPreWidget(),
    )

    def clean_path(self):
        """Allow only valid regex expression, if selected"""
        is_regex = self.cleaned_data.get('is_regex', False)
        path = self.cleaned_data.get('path')
        if is_regex:
            try:
                re.compile(path)
            except re.error:
                raise forms.ValidationError("Regular expression not valid. ")
        return path

    def occurences_list(self, instance):
        """Show the user sample results, usable for experiments with regexes."""
        results = []
        if instance.is_regex:
            compiled = re.compile(instance.path)
            for ch in CIChangeGit.objects.all():
                for path in ch.file_paths.split('#'):
                    if compiled.match(path):
                        results.append(path)
        else:
            search_path = instance.path
            for ch in CIChangeGit.objects.all():
                for path in ch.file_paths.split('#'):
                    if search_path in path:
                        results.append(path)
        return '\n'.join(results)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            self.base_fields['occurences'].initial = self.occurences_list(instance)
        super(GitPathMappingAdminForm, self).__init__(*args, **kwargs)


class GitPathMappingAdmin(ModelAdmin):
    form = GitPathMappingAdminForm
    list_display = ('ci', 'path', 'is_regex')
    search_fields = ('ci', 'is_regex', 'path',)
    save_on_top = True


admin.site.register(db.GitPathMapping, GitPathMappingAdmin)


class CIOwnerAdmin(ModelAdmin):
    list_display = ('last_name', 'first_name', 'email')
    search_fields = ('last_name', 'first_name', 'email')
    save_on_top = True


admin.site.register(db.CIOwner, CIOwnerAdmin)


# simple types
admin.site.register([
    db.CI,
    db.CIType,
    db.CILayer,
    db.CIRelation,
    db.CIAttribute,
    db.CIAttributeValue,
])
