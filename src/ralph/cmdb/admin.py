#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from lck.django.common.admin import ModelAdmin

from ajax_select.fields import AutoCompleteSelectField

import ralph.cmdb.models as db
from ralph.cmdb.models_changes import CIChangeGit
from ralph.cmdb.updater import update_cis_layers
from ralph.ui.widgets import ReadOnlyPreWidget


TRACKED_APPS = ('discovery', 'business',)


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


class CILayerForm(forms.ModelForm):
    class Meta:
        model = db.CILayer

    def save(self, commit=True):
        model = super(CILayerForm, self).save(commit)
        if self.has_changed():
            current_content_types = set(self.initial.get('content_types', []))
            new_content_types = set([
                content_type.id
                for content_type in self.cleaned_data.get('content_types', [])
            ])
            if not (current_content_types == new_content_types):
                touched_content_types = current_content_types.union(
                    new_content_types,
                )
                update_cis_layers(
                    touched_content_types,
                    [
                        item.id for item in self.cleaned_data.get(
                            'content_types',
                            [],
                        )
                    ],
                    model,
                )
        return model


class CILayerAdmin(ModelAdmin):
    form = CILayerForm
    filter_horizontal = ('content_types',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "content_types":
            kwargs["queryset"] = ContentType.objects.filter(
                app_label__in=TRACKED_APPS,
            ).order_by('name')
        return super(CILayerAdmin, self).formfield_for_manytomany(
            db_field,
            request,
            **kwargs
        )

admin.site.register(db.CILayer, CILayerAdmin)


# simple types
admin.site.register([
    db.CI,
    db.CIType,
    db.CIRelation,
    db.CIAttribute,
    db.CIAttributeValue,
])
