#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.data_table import DataTableMixin, DataTableColumn
from bob.menu import MenuItem, MenuHeader

from ralph.cmdb.models import (
    CI_CHANGE_TYPES,
    ArchivedCIChange,
    ArchivedCIChangeZabbixTrigger,
    ArchivedCIChangeGit,
    ArchivedCIChangePuppet,
    ArchivedCIChangeSOIncident,
    ArchivedCIChangeCMDBHistory,
)
from ralph.cmdb.views import BaseCMDBView


class BaseCMDBArchiveView(BaseCMDBView, DataTableMixin):
    template_name = 'cmdb/archive.html'
    sort_variable_name = 'sort'
    export_variable_name = None
    rows_per_page = 10
    model = None

    def get_sidebar_items(self):
        sidebar_items = (
            [MenuHeader('CMDB Archive')] +
            [
                MenuItem(
                    label='Asset attr. changes',
                    fugue_icon='fugue-wooden-box--arrow',
                    href='/cmdb/archive/assets/',
                ),
                MenuItem(
                    label='CI attributes changes',
                    fugue_icon='fugue-puzzle',
                    href='/cmdb/archive/cmdb/',
                ),
                MenuItem(
                    label='Monitoring events',
                    fugue_icon='fugue-thermometer',
                    href='/cmdb/archive/zabbix/',
                ),
                MenuItem(
                    label='Repo changes',
                    fugue_icon='fugue-git',
                    href='/cmdb/archive/git/',
                ),
                MenuItem(
                    label='Agent events',
                    fugue_icon='fugue-flask',
                    href='/cmdb/archive/puppet/',
                ),
                MenuItem(
                    label='Status Office events',
                    fugue_icon='fugue-plug',
                    href='/cmdb/archive/so/',
                ),
                MenuItem(
                    label='Back to CMDB',
                    fugue_icon='fugue-arrow-return-180',
                    href='/cmdb/changes/timeline',
                )
            ]
        )
        return sidebar_items

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseCMDBArchiveView, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update(
            super(BaseCMDBArchiveView, self).get_context_data_paginator(
                *args,
                **kwargs
            ),
        )
        ret.update({
            'sort_variable_name': self.sort_variable_name,
            'url_query': self.request.GET,
            'sort': self.sort,
            'columns': self.columns,
        })
        return ret

    def get_query(self):
        items = self.model.objects.all()
        self.data_table_query(items)

    def get(self, *args, **kwargs):
        self.get_query()
        if self.export_requested():
            return self.response
        return super(BaseCMDBView, self).get(*args, **kwargs)


class ArchivedAssetsChanges(BaseCMDBArchiveView):
    model = ArchivedCIChange
    columns = [
        DataTableColumn(
            'CI',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Created',
            field='created',
            sort_expression='created',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Time',
            field='time',
            sort_expression='time',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'User',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Field name',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Old value',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'New value',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Message',
            bob_tag=True,
            export=True,
        ),
    ]

    def get_query(self):
        items = self.model.objects.filter(type=CI_CHANGE_TYPES.DEVICE)
        self.data_table_query(items)

    def get_context_data(self, *args, **kwargs):
        ret = super(ArchivedAssetsChanges, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update({
            'mode': 'assets',
            'section_name': 'Asset attributes changes',
        })
        return ret


class ArchivedZabbixTriggers(BaseCMDBArchiveView):
    model = ArchivedCIChangeZabbixTrigger
    columns = [
        DataTableColumn(
            'CI',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Created',
            field='created',
            sort_expression='created',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Host',
            field='host',
            sort_expression='host',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Status',
            field='status',
            sort_expression='status',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Priority',
            field='priority',
            sort_expression='priority',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Description',
            field='description',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Last Change',
            field='lastchange',
            sort_expression='lastchange',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Comments',
            field='comments',
            bob_tag=True,
            export=True,
        ),
    ]

    def get_context_data(self, *args, **kwargs):
        ret = super(ArchivedZabbixTriggers, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update({
            'mode': 'zabbix',
            'section_name': 'Monitoring events',
        })
        return ret


class ArchivedGitChanges(BaseCMDBArchiveView):
    model = ArchivedCIChangeGit
    columns = [
        DataTableColumn(
            'CI',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Created',
            field='created',
            sort_expression='created',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Time',
            field='time',
            sort_expression='time',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Fila path',
            field='file_paths',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Comment',
            field='comment',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Author',
            field='author',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Changeset',
            field='changeset',
            bob_tag=True,
            export=True,
        ),
    ]

    def get_context_data(self, *args, **kwargs):
        ret = super(ArchivedGitChanges, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update({
            'mode': 'git',
            'section_name': 'Repo changes',
        })
        return ret


class ArchivedPuppetChanges(BaseCMDBArchiveView):
    model = ArchivedCIChangePuppet
    columns = [
        DataTableColumn(
            'CI',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Created',
            field='created',
            sort_expression='created',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Time',
            field='time',
            sort_expression='time',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Configuration Version',
            field='configuration_version',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Host',
            field='host',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Kind',
            field='kind',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Status',
            field='status',
            bob_tag=True,
            export=True,
        ),
    ]

    def get_context_data(self, *args, **kwargs):
        ret = super(ArchivedPuppetChanges, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update({
            'mode': 'puppet',
            'section_name': 'Agent events',
        })
        return ret


class ArchivedStatusOfficeIncidents(BaseCMDBArchiveView):
    model = ArchivedCIChangeSOIncident
    columns = [
        DataTableColumn(
            'CI',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Created',
            field='created',
            sort_expression='created',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Time',
            field='time',
            sort_expression='time',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Status',
            field='status',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Subject',
            field='subject',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'incident_id',
            field='incident_id',
            bob_tag=True,
            export=True,
        ),
    ]

    def get_context_data(self, *args, **kwargs):
        ret = super(ArchivedStatusOfficeIncidents, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update({
            'mode': 'so',
            'section_name': 'Incidents',
        })
        return ret


class ArchivedCIAttributesChanges(BaseCMDBArchiveView):
    model = ArchivedCIChangeCMDBHistory
    columns = [
        DataTableColumn(
            'CI',
            field='ci',
            sort_expression='ci',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Created',
            field='created',
            sort_expression='created',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Time',
            field='time',
            sort_expression='time',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'User',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Field name',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Old value',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'New value',
            bob_tag=True,
            export=True,
        ),
        DataTableColumn(
            'Comment',
            bob_tag=True,
            export=True,
        ),
    ]

    def get_context_data(self, *args, **kwargs):
        ret = super(ArchivedCIAttributesChanges, self).get_context_data(
            *args,
            **kwargs
        )
        ret.update({
            'mode': 'cmdb',
            'section_name': 'CI attributes changes',
        })
        return ret
