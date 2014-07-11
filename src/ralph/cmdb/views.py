#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import re
from urlparse import urljoin

from bob.data_table import DataTableMixin
from bob.menu import MenuItem, MenuHeader

from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils import simplejson
from django.utils.html import escape
from django.conf import settings
from django.core.urlresolvers import reverse

from lck.cache.memoization import memoize
from lck.django.common import nested_commit_on_success
from lck.django.filters import slugify

from ralph.account.models import Perm, ralph_permission

from ralph.cmdb.forms import (
    CISearchForm,
    CIEditForm,
    CIViewForm,
    CIRelationEditForm,
    SearchImpactForm,
)
from ralph.cmdb.models_ci import (
    CILayer,
    CI_TYPES,
    CI,
    CIRelation,
    CIType,
    CI_STATE_TYPES,
)
import ralph.cmdb.models as db
from ralph.cmdb.graphs import ImpactCalculator
from ralph.ui.views.common import Base
from ralph.cmdb.forms import (
    ReportFilters,
    ReportFiltersDateRange,
)
from ralph.cmdb.util import report_filters, add_filter, table_colums, collect

JIRA_URL = urljoin(settings.ISSUETRACKERS['default']['URL'], 'browse')
ROWS_PER_PAGE = 20
SAVE_PRIORITY = 200


class BaseCMDBView(Base):
    template_name = 'nope.html'
    Form = CIRelationEditForm

    def generate_breadcrumb(self):
        parent = self.request.GET.get('parent', '')
        if not parent:
            return []
        list = []
        counter = 0
        while parent and counter < 100:
            ci = db.CI.objects.filter(id=parent).all()[0]
            list.insert(0, ci)
            try:
                parent = db.CI.objects.filter(parent__child=parent).all()[0].id
            except:
                parent = None
            if parent == ci.id:
                parent = None
            counter += 1
        return list

    @memoize(skip_first=True, update_interval=60)
    def get_permissions_dict(self, user_id):
        has_perm = User.objects.get(pk=user_id).get_profile().has_perm
        ci_perms = [
            'create_configuration_item',
            'edit_configuration_item_info_generic',
            'edit_configuration_item_relations',
            'read_configuration_item_info_generic',
            'read_configuration_item_info_puppet',
            'read_configuration_item_info_git',
            'read_configuration_item_info_jira',
        ]
        ret = {}
        for perm in ci_perms:
            ret.update({perm + '_perm': has_perm(getattr(Perm, perm))})
        return ret

    def _get_sidebar_layers_items(self):
        return [
            (
                '/cmdb/search?layer=%d' % layer.id,
                layer.name,
                layer.icon.raw if layer.icon else 'fugue-layers-stack-arrange',
            ) for layer in CILayer.objects.order_by('name')
        ]

    def get_sidebar_items(self):
        ci = (
            ('/cmdb/add', 'Add CI', 'fugue-block--plus'),
            ('/cmdb/changes/dashboard', 'Dashboard', 'fugue-dashboard'),
            ('/cmdb/graphs', 'Impact report', 'fugue-dashboard'),
            ('/cmdb/changes/timeline', 'Timeline View', 'fugue-dashboard'),
            ('/admin/cmdb', 'Admin', 'fugue-toolbox'),
            ('/cmdb/cleanup', 'Clean up', 'fugue-broom'),
        )
        layers = (
            ('/cmdb/search', 'All Cis (all layers)', 'fugue-magnifier'),
        )
        layers += tuple(self._get_sidebar_layers_items())
        reports = (
            ('/cmdb/changes/reports?kind=top_changes',
                'Top CI changes', 'fugue-reports'),
            ('/cmdb/changes/reports?kind=top_problems',
                'Top CI problems', 'fugue-reports'),
            ('/cmdb/changes/reports?kind=top_incidents',
                'Top CI incidents', 'fugue-reports'),
            ('/cmdb/changes/reports?kind=usage',
                'Cis w/o changes', 'fugue-reports'),
        )
        events = (
            ('/cmdb/changes/changes', 'All Events', 'fugue-arrow'),
            ('/cmdb/changes/changes?type=3', 'Asset attr. changes',
                'fugue-wooden-box--arrow'),
            ('/cmdb/changes/changes?type=4', 'Monitoring events',
                'fugue-thermometer'),
            ('/cmdb/changes/changes?type=1', 'Repo changes',
                'fugue-git'),
            ('/cmdb/changes/changes?type=2', 'Agent events',
                'fugue-flask'),
            ('/cmdb/changes/incidents', 'Incidents',
                'fugue-question'),
            ('/cmdb/changes/problems', 'Problems',
                'fugue-bomb'),
            ('/cmdb/changes/jira_changes', 'Jira Changes',
                'fugue-arrow-retweet'),
        )
        sidebar_items = (
            [MenuHeader('Configuration Items')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in ci] +
            [MenuHeader('CI by Layers')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in layers] +
            [MenuHeader('Reports')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in reports] +
            [MenuHeader('Events and  Changes')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in events] +
            [MenuHeader('Other')] +
            [MenuItem(
                label='Archive',
                fugue_icon='fugue-vise-drawer',
                href='/cmdb/archive/assets/',
            )]
        )
        return sidebar_items

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        ret.update(self.get_permissions_dict(self.request.user.id))
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
            'breadcrumbs': self.generate_breadcrumb(),
            'url_query': self.request.GET,
            'span_number': '6',
            'ZABBIX_URL': settings.ZABBIX_URL,
            'SO_URL': settings.SO_URL,
            'tabs_left': False,
            'fisheye_url': settings.FISHEYE_URL,
            'fisheye_project': settings.FISHEYE_PROJECT_NAME,
            'section': 'cmdb',
        })
        return ret


def _get_pages(paginator, page):
    pages = paginator.page_range[
        max(0, page - 4):min(paginator.num_pages, page + 3)
    ]
    if 1 not in pages:
        pages.insert(0, 1)
        pages.insert(1, '...')
    if paginator.num_pages not in pages:
        pages.append('...')
        pages.append(paginator.num_pages)
    return pages


def get_error_title(form):
    return ', '.join(
        form.errors.get('__all__', []),
    ) or 'Correct the errors.' if form.errors else ''


class EditRelation(BaseCMDBView):
    template_name = 'cmdb/edit_relation.html'
    Form = CIRelationEditForm

    form_options = dict(
        label_suffix='',
        prefix='base',
    )

    def get_context_data(self, **kwargs):
        ret = super(EditRelation, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
        })
        return ret

    def get(self, *args, **kwargs):
        if not self.get_permissions_dict(self.request.user.id).get(
                'edit_configuration_item_relations_perm', False):
            return HttpResponseForbidden()
        rel_id = kwargs.get('relation_id')
        rel = get_object_or_404(db.CIRelation, id=rel_id)
        self.form_options['instance'] = rel
        self.form = self.Form(**self.form_options)
        self.rel_parent = rel.parent
        self.rel_child = rel.child
        self.rel_type = rel.type
        self.rel = rel
        return super(EditRelation, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        self.form = None
        self.rel = None
        rel_id = kwargs.get('relation_id')
        rel = get_object_or_404(db.CIRelation, id=rel_id)
        self.form_options['instance'] = rel

        ci_id = kwargs.get('ci_id')
        if ci_id:
            # remove relation
            ci_relation = db.CIRelation.objects.filter(id=rel_id).all()
            ci_relation.delete()
            return HttpResponse('ok')
        if self.Form:
            self.form = self.Form(self.request.POST, **self.form_options)
            if self.form.is_valid():
                ci_id = self.kwargs.get('ci_id')
                model = self.form.save(commit=False)
                model.save(user=self.request.user)
                return HttpResponseRedirect('/cmdb/edit/%s' % ci_id)
            else:
                error_title = get_error_title(self.form)
                messages.error(self.request, _(error_title))
        return super(EditRelation, self).get(*args, **kwargs)


class AddRelation(BaseCMDBView):
    template_name = 'cmdb/add_relation.html'
    Form = CIRelationEditForm

    form_options = dict(
        label_suffix='',
        prefix='base',
    )

    def get_context_data(self, **kwargs):
        ret = super(AddRelation, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'relations_parent': self.relations_parent,
            'relations_child': self.relations_child,
        })
        return ret

    def form_initial(self):
        data = {
            'parent': self.rel_parent,
            'child': self.rel_child,
        }
        return data

    def get(self, *args, **kwargs):
        if not self.get_permissions_dict(self.request.user.id).get(
                'edit_configuration_item_relations_perm',
                False):
            return HttpResponseForbidden()
        self.rel_parent = self.request.GET.get('rel_parent')
        self.rel_child = self.request.GET.get('rel_child')
        ci_id = kwargs.get('ci_id')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.relations_parent = [
            x.child for x in db.CIRelation.objects.filter(parent=ci_id)
        ]
        self.relations_child = [
            x.parent for x in db.CIRelation.objects.filter(child=ci_id)
        ]
        self.form_options['initial'] = self.form_initial()
        self.form = self.Form(**self.form_options)
        return super(AddRelation, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        self.form = None
        self.rel = None
        ci_id = kwargs.get('ci_id')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.relations_parent = db.CIRelation.objects.filter(
            parent=ci_id,
        )
        self.relations_child = db.CIRelation.objects.filter(
            child=ci_id,
        )
        if self.Form:
            self.form = self.Form(self.request.POST, **self.form_options)
            if self.form.is_valid():
                ci_id = self.kwargs.get('ci_id')
                model = self.form.save(commit=False)
                model.save(user=self.request.user)
                return HttpResponseRedirect('/cmdb/ci/edit/%s' % ci_id)
            else:
                error_title = get_error_title(self.form)
                messages.error(self.request, _(error_title))
        return super(AddRelation, self).get(*args, **kwargs)


class Add(BaseCMDBView):
    template_name = 'cmdb/add_ci.html'
    Form = CIEditForm
    form_options = dict(
        label_suffix='',
        prefix='base',
    )

    def get_context_data(self, **kwargs):
        ret = super(Add, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'label': 'Add CI',
            'subsection': 'Add CI',
            'sidebar_selected': 'add ci',
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = self.Form(**self.form_options)
        return super(Add, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        self.form = None
        self.ci = None
        if self.Form:
            self.form = self.Form(self.request.POST, **self.form_options)
            if self.form.is_valid():
                model = self.form.save()
                if not model.content_object:
                    model.uid = "%s-%s" % ('mm', model.id)
                    model.save(user=self.request.user)
                messages.success(self.request, _("Changes saved."))
                return HttpResponseRedirect(
                    '/cmdb/ci/edit/' + unicode(model.id),
                )
            else:
                messages.error(self.request, _("Correct the errors."))

        return super(Add, self).get(*args, **kwargs)


class LastChanges(BaseCMDBView):
    template_name = 'cmdb/search_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(LastChanges, self).get_context_data(**kwargs)
        ret.update({
            'last_changes': self.last_changes,
            'jira_url': JIRA_URL,
        })
        return ret

    def get_last_changes(self, ci):
        from ralph.cmdb.integration.jira import Jira
        params = dict(jql='DB\\ CI="%s"' % self.ci_uid)
        xxx = Jira().find_issues(params)
        items_list = []
        for i in xxx.get('issues'):
            f = i.get('fields')
            items_list.append(dict(
                key=i.get('key'),
                description=f.get('description'),
                summary=f.get('summary'),
                assignee=f.get('assignee').get('displayName'))),
        return items_list

    def get(self, *args, **kwargs):
        self.ci_uid = kwargs.get('ci_id', None)
        self.last_changes = self.get_last_changes(self.ci_uid)
        return super(LastChanges, self).get(*args, **kwargs)


class BaseCIDetails(BaseCMDBView):
    template_name = 'cmdb/ci_details.html'

    def check_perm(self):
        if not self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_generic_perm',
            False,
        ):
            return HttpResponseForbidden()

    def get_tabs(self):
        tabs = [
            ('Basic Info', 'main'),
            ('Relations', 'relations'),
        ]
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_git_perm',
            False
        ):
            tabs.append(('Repo changes', 'git'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_puppet_perm',
            False
        ):
            tabs.append(('Agent events', 'puppet'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False
        ):
            tabs.append(('Asset attr. changes', 'ralph'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False
        ):
            tabs.append(('CI attr. changes', 'ci_changes'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False
        ):
            tabs.append(('Monitoring events', 'zabbix'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False
        ):
            tabs.append(('Problems', 'problems'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False
        ):
            tabs.append(('Incidents', 'incidents'))
        if self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False
        ):
            tabs.append(('Jira Changes', 'jira_changes'))
        return tabs

    def generate_breadcrumb(self):
        if getattr(self, 'ci'):
            parent_id = self.ci.id
        else:
            return []
        breadcrumbs = []
        counter = 0
        while parent_id and counter < 100:
            try:
                ci = db.CI.objects.filter(id=parent_id).all()[0]
            except IndexError:
                break
            breadcrumbs.insert(0, ci)
            try:
                parent_id = db.CI.objects.filter(
                    parent__child=parent_id
                ).all()[0].id
            except IndexError:
                parent_id = None
            if parent_id == ci.id:
                parent_id = None
            counter += 1
        return breadcrumbs

    def get_messages(self):
        days = datetime.timedelta(days=7)
        last_week_puppet_errors = db.CIChangePuppet.objects.filter(
            ci=self.ci,
            time__range=(
                datetime.datetime.now(), datetime.datetime.now() - days)
        ).count()
        incidents = db.CIIncident.objects.filter(
            cis=self.ci,
        ).count()
        problems = db.CIProblem.objects.filter(
            cis=self.ci,
        ).count()
        messages = []
        if last_week_puppet_errors:
            messages.append(dict(
                message="Puppet reported %d errors since last week." % (
                    last_week_puppet_errors),
                title='Warning',
                type='warning',
            ))
        if incidents:
            messages.append(dict(
                message="This CI has %d incidents." % (incidents),
                title='Be carefull.',
                type='error',
            ))
        if problems:
            messages.append(dict(
                message="This CI has %d problems." % (problems),
                title='Be carefull.',
                type='error',
            ))
        return messages

    def get_ci_id(self):
        # 2 types of id can land here
        ci_id = self.kwargs.get('ci_id')
        if ci_id.find('-') >= 0:
            ci = db.CI.objects.get(uid=ci_id)
            return ci.id
        else:
            return self.kwargs.get('ci_id', None)

    def initialize_vars(self):
        self.tabs = self.get_tabs()
        path = self.request.path
        if self.request.path.endswith('/'):
            path = self.request.path
        else:
            path = '%s/' % self.request.path
        if not re.search(r'[0-9]+/$', path):
            path = '%s../' % path
        self.base_ci_link = path

    def get_context_data(self, **kwargs):
        ret = super(BaseCIDetails, self).get_context_data(**kwargs)
        ret.update({
            'tabs': self.tabs,
            'active_tab': self.active_tab,
            'base_ci_link': self.base_ci_link,
            'label': 'Edit CI: {} (uid: {})'.format(self.ci.name, self.ci.uid),
            'subsection': 'Edit - %s' % self.ci.name,
            'ci': self.ci,
            'ci_id': self.ci.id,
            'uid': self.ci.uid,
            'cmdb_messages': self.get_messages(),
        })
        return ret


def _update_labels(items, ci):
    items.update({
        'label': 'View CI: {} (uid: {})'.format(ci.name, ci.uid),
        'subsection': 'Info - %s' % ci.name,
    })
    return items


class MainCIEdit(BaseCIDetails):
    template_name = 'cmdb/ci_edit.html'
    active_tab = 'main'
    Form = CIEditForm
    form_options = dict(label_suffix='', prefix='base')

    def initialize_vars(self):
        super(MainCIEdit, self).initialize_vars()
        self.show_in_ralph = False
        self.ralph_ci_link = ''

    def get_context_data(self, **kwargs):
        ret = super(MainCIEdit, self).get_context_data(**kwargs)
        ret.update({
            'show_in_ralph': self.show_in_ralph,
            'ralph_ci_link': self.ralph_ci_link,
            'service_name': getattr(self, 'service_name', None),
            'editable': True,
            'form': self.form,
        })
        return ret

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            if (
                self.ci.content_object and
                self.ci.content_type.name == 'device'
            ):
                self.show_in_ralph = True
                self.ralph_ci_link = "/ui/search/info/%d" % (
                    self.ci.content_object.id
                )
            self.service_name = self.get_first_parent_venture_name(ci_id)
            self.form_options['instance'] = self.ci
            # self.form_options['initial'] = self.form_initial(self.ci)
        self.form = self.Form(**self.form_options)
        return super(MainCIEdit, self).get(*args, **kwargs)

    @nested_commit_on_success
    def post(self, *args, **kwargs):
        self.initialize_vars()
        ci_id = self.kwargs.get('ci_id')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            self.form_options['instance'] = self.ci
            self.form = self.Form(
                self.request.POST, **self.form_options
            )
            if self.form.is_valid():
                model = self.form.save(commit=False)
                model.id = self.ci.id
                model.save(user=self.request.user)
                messages.success(self.request, "Changes saved.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Correct the errors.")
        return super(MainCIEdit, self).get(*args, **kwargs)

    def get_first_parent_venture_name(self, ci_id):
        cis = db.CI.objects.filter(
            relations__parent__child=ci_id,
            relations__parent__parent__type=db.CI_TYPES.VENTUREROLE.id,
        ).all()
        if cis:
            return cis[0].name


class MainCIView(MainCIEdit):
    Form = CIViewForm

    def get_context_data(self, **kwargs):
        ret = super(MainCIView, self).get_context_data(**kwargs)
        ret = _update_labels(ret, self.ci)
        ret.update({
            'editable': False,
        })
        return ret

    def post(self, *args, **kwargs):
        return HttpResponseForbidden()


class CIRelationsEdit(BaseCIDetails):
    template_name = 'cmdb/ci_relations.html'
    active_tab = 'relations'

    def get_context_data(self, **kwargs):
        ret = super(CIRelationsEdit, self).get_context_data(**kwargs)
        ret.update({
            'relations_contains': self.relations_contains,
            'relations_requires': self.relations_requires,
            'relations_isrequired': self.relations_isrequired,
            'relations_parts': self.relations_parts,
            'relations_hasrole': self.relations_hasrole,
            'relations_isrole': self.relations_isrole,
            'editable': True,
        })
        return ret

    def initialize_vars(self):
        super(CIRelationsEdit, self).initialize_vars()
        self.relations_contains = []
        self.relations_parts = []
        self.relations_requires = []
        self.relations_isrequired = []
        self.relations_hasrole = []
        self.relations_isrole = []

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            self.calculate_relations(ci_id)
        return super(CIRelationsEdit, self).get(*args, **kwargs)

    def calculate_relations(self, ci_id):
        self.relations_contains = [
            (x, x.child, x.child.icon)
            for x in db.CIRelation.objects.filter(
                parent=ci_id, type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_parts = [
            (x, x.parent, x.parent.icon)
            for x in db.CIRelation.objects.filter(
                child=ci_id,
                type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_requires = [
            (x, x.child, x.parent.icon)
            for x in db.CIRelation.objects.filter(
                parent=ci_id, type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_isrequired = [
            (x, x.parent, x.parent.icon)
            for x in db.CIRelation.objects.filter(
                child=ci_id, type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_hasrole = [
            (x, x.child, x.parent.icon)
            for x in db.CIRelation.objects.filter(
                parent=ci_id, type=db.CI_RELATION_TYPES.HASROLE.id)
        ]
        self.relations_isrole = [
            (x, x.parent, x.parent.icon)
            for x in db.CIRelation.objects.filter(
                child=ci_id, type=db.CI_RELATION_TYPES.HASROLE.id)
        ]


class CIRelationsView(CIRelationsEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIRelationsView, self).get_context_data(**kwargs)
        ret = _update_labels(ret, self.ci)
        ret.update({
            'editable': False,
        })
        return ret


class CIGitEdit(BaseCIDetails):
    template_name = 'cmdb/ci_git.html'
    active_tab = 'git'

    def check_perm(self):
        if not self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_git_perm',
            False,
        ):
            return HttpResponseForbidden()

    def initialize_vars(self):
        super(CIGitEdit, self).initialize_vars()
        self.git_changes = []

    def get_context_data(self, **kwargs):
        ret = super(CIGitEdit, self).get_context_data(**kwargs)
        ret.update({
            'label': 'Edit CI: {} (uid: {})'.format(self.ci.name, self.ci.uid),
            'subsection': 'Edit - %s' % self.ci.name,
            'git_changes': self.git_changes,
        })
        return ret

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            try:
                page = int(self.request.GET.get('page', 1))
            except ValueError:
                page = 1
            query = db.CIChange.objects.filter(
                ci=self.ci,
                type=db.CI_CHANGE_TYPES.CONF_GIT.id,
            )
            paginator = Paginator(query, 20)
            self.git_changes = paginator.page(page)
            object_list = []
            for item in self.git_changes.object_list:
                object_list.append(item.content_object)
            self.git_changes.object_list = object_list
        return super(CIGitEdit, self).get(*args, **kwargs)


class CIGitView(CIGitEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIGitView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class CIPuppetEdit(BaseCIDetails):
    template_name = 'cmdb/ci_puppet.html'
    active_tab = 'puppet'

    def check_perm(self):
        if not self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_puppet_perm',
            False,
        ):
            return HttpResponseForbidden()

    def initialize_vars(self):
        super(CIPuppetEdit, self).initialize_vars()
        self.puppet_reports = []

    def get_context_data(self, **kwargs):
        ret = super(CIPuppetEdit, self).get_context_data(**kwargs)
        ret.update({
            'puppet_reports': self.puppet_reports,
        })
        return ret

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            try:
                page = int(self.request.GET.get('page', 1))
            except ValueError:
                page = 1
            query = db.CIChangePuppet.objects.filter(ci=self.ci).all()
            paginator = Paginator(query, 10)
            self.puppet_reports = paginator.page(page)
            object_list = []
            for report in self.puppet_reports.object_list:
                puppet_logs = db.PuppetLog.objects.filter(
                    cichange=report
                ).all()
                object_list.append(
                    dict(report=report, logs=puppet_logs)
                )
            self.puppet_reports.object_list = object_list
        return super(CIPuppetEdit, self).get(*args, **kwargs)


class CIPuppetView(CIPuppetEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIPuppetView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class CIRalphEdit(BaseCIDetails):
    template_name = 'cmdb/ci_ralph.html'
    active_tab = 'ralph'

    def check_perm(self):
        if not self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False,
        ):
            return HttpResponseForbidden()

    def initialize_vars(self):
        super(CIRalphEdit, self).initialize_vars()
        self.device_attributes_changes = []

    def get_context_data(self, **kwargs):
        ret = super(CIRalphEdit, self).get_context_data(**kwargs)
        ret.update({
            'device_attributes_changes': self.device_attributes_changes,
        })
        return ret

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            try:
                page = int(self.request.GET.get('page', 1))
            except ValueError:
                page = 1
            query = db.CIChange.objects.filter(
                ci=self.ci,
                type=db.CI_CHANGE_TYPES.DEVICE.id,
            )
            paginator = Paginator(query, 20)
            self.device_attributes_changes = paginator.page(page)
            object_list = []
            for item in self.device_attributes_changes.object_list:
                object_list.append(item.content_object)
            self.device_attributes_changes.object_list = object_list
        return super(CIRalphEdit, self).get(*args, **kwargs)


class CIRalphView(CIRalphEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIRalphView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class CIChangesEdit(BaseCIDetails):
    template_name = 'cmdb/ci_changes.html'
    active_tab = 'ci_changes'

    def check_perm(self):
        if not self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False,
        ):
            return HttpResponseForbidden()

    def initialize_vars(self):
        super(CIChangesEdit, self).initialize_vars()
        self.ci_attributes_changes = []

    def get_context_data(self, **kwargs):
        ret = super(CIChangesEdit, self).get_context_data(**kwargs)
        ret.update({
            'ci_attributes_changes': self.ci_attributes_changes,
        })
        return ret

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            try:
                page = int(self.request.GET.get('page', 1))
            except ValueError:
                page = 1
            query = db.CIChange.objects.filter(
                ci=self.ci,
                type=db.CI_CHANGE_TYPES.CI.id,
            ).order_by('time')
            paginator = Paginator(query, 20)
            self.ci_attributes_changes = paginator.page(page)
            object_list = []
            for item in self.ci_attributes_changes.object_list:
                object_list.append(item.content_object)
            self.ci_attributes_changes.object_list = object_list
        return super(CIChangesEdit, self).get(*args, **kwargs)


class CIChangesView(CIChangesEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIChangesView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class CIZabbixEdit(BaseCIDetails):
    template_name = 'cmdb/ci_zabbix.html'
    active_tab = 'zabbix'

    def check_perm(self):
        if not self.get_permissions_dict(self.request.user.id).get(
            'read_configuration_item_info_jira_perm',
            False,
        ):
            return HttpResponseForbidden()

    def initialize_vars(self):
        super(CIZabbixEdit, self).initialize_vars()
        self.zabbix_triggers = []

    def get_context_data(self, **kwargs):
        ret = super(CIZabbixEdit, self).get_context_data(**kwargs)
        ret.update({
            'zabbix_triggers': self.zabbix_triggers,
        })
        return ret

    def get(self, *args, **kwargs):
        perm = self.check_perm()
        if perm:
            return perm
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            # CI doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            try:
                page = int(self.request.GET.get('page', 1))
            except ValueError:
                page = 1
            query = db.CIChangeZabbixTrigger.objects.filter(
                ci=self.ci,
            ).order_by('-lastchange')
            paginator = Paginator(query, 20)
            self.zabbix_triggers = paginator.page(page)
        return super(CIZabbixEdit, self).get(*args, **kwargs)


class CIZabbixView(CIZabbixEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIZabbixView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class CIProblemsEdit(BaseCIDetails, DataTableMixin):
    template_name = 'cmdb/ci_changes_tab.html'
    active_tab = 'problems'
    sort_variable_name = 'sort'
    export_variable_name = None  # fix in bob!
    columns = table_colums()
    perms = [
        {
            'perm': Perm.read_configuration_item_info_jira,
            'msg': _("You don't have permission to see that."),
        },
    ]

    def initialize_vars(self):
        super(CIProblemsEdit, self).initialize_vars()
        self.problems = []

    def get_context_data(self, *args, **kwargs):
        ret = super(CIProblemsEdit, self).get_context_data(**kwargs)
        ret.update(
            super(CIProblemsEdit, self).get_context_data_paginator(
                *args,
                **kwargs
            )
        )
        ret.update({
            'sort_variable_name': self.sort_variable_name,
            'url_query': self.request.GET,
            'sort': self.sort,
            'columns': self.columns,
            'jira_url': JIRA_URL,
            'form': {
                'filters': ReportFilters(self.request.GET),
                'date_range': ReportFiltersDateRange(self.request.GET),
            },
            'possible_title': _('Problems that could affect this CI'),
            'possible_data': collect(
                self.ci,
                self.get_events,
                up=False,
                exclusive=True,
            ),
        })
        return ret

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.data_table_query(
            report_filters(
                cls=db.CIProblem,
                order='-update_date',
                filters=add_filter(self.request.GET, cis=self.ci),
            )
        )
        return super(CIProblemsEdit, self).get(*args, **kwargs)

    def get_events(self, ci):
        return db.CIProblem.objects.filter(
            cis=ci,
            update_date__gte=(
                datetime.datetime.now() -
                settings.POSSIBLE_EVENTS_TIMEDELTA
            ),
        )


class CIProblemsView(CIProblemsEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIProblemsView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class JiraChangesEdit(BaseCIDetails, DataTableMixin):
    template_name = 'cmdb/ci_changes_tab.html'
    active_tab = 'jira_changes'
    sort_variable_name = 'sort'
    export_variable_name = None  # fix in bob!
    columns = table_colums()
    perms = [
        {
            'perm': Perm.read_configuration_item_info_jira,
            'msg': _("You don't have permission to see that."),
        },
    ]

    def initialize_vars(self):
        super(JiraChangesEdit, self).initialize_vars()
        self.jira_changes = []

    def get_events(self, ci):
        return db.JiraChanges.objects.filter(
            cis=ci,
            update_date__gte=(
                datetime.datetime.now() -
                settings.POSSIBLE_EVENTS_TIMEDELTA
            ),
        )

    def get_context_data(self, *args, **kwargs):
        ret = super(JiraChangesEdit, self).get_context_data(**kwargs)
        ret.update(
            super(JiraChangesEdit, self).get_context_data_paginator(
                *args,
                **kwargs
            )
        )
        ret.update({
            'sort_variable_name': self.sort_variable_name,
            'url_query': self.request.GET,
            'sort': self.sort,
            'columns': self.columns,
            'jira_url': JIRA_URL,
            'form': {
                'filters': ReportFilters(self.request.GET),
                'date_range': ReportFiltersDateRange(self.request.GET),
            },
            'possible_title': _('Changes that could affect this CI'),
            'possible_data': collect(
                self.ci,
                self.get_events,
                up=False,
                exclusive=True,
            ),
        })
        return ret

    @ralph_permission(perms)
    def get(self, *args, **kwargs):
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.data_table_query(
            report_filters(
                cls=db.JiraChanges,
                order='-update_date',
                filters=add_filter(
                    self.request.GET,
                    cis=self.ci,
                ),
            )
        )
        return super(JiraChangesEdit, self).get(*args, **kwargs)


class JiraChangesView(JiraChangesEdit):

    def get_context_data(self, **kwargs):
        ret = super(JiraChangesView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class CIIncidentsEdit(BaseCIDetails, DataTableMixin):
    template_name = 'cmdb/ci_changes_tab.html'
    active_tab = 'incidents'
    sort_variable_name = 'sort'
    export_variable_name = None  # fix in bob!
    columns = table_colums()
    perms = [
        {
            'perm': Perm.read_configuration_item_info_jira,
            'msg': _("You don't have permission to see that."),
        },
    ]

    def initialize_vars(self):
        super(CIIncidentsEdit, self).initialize_vars()
        self.incidents = []

    def get_context_data(self, *args, **kwargs):
        ret = super(CIIncidentsEdit, self).get_context_data(**kwargs)
        ret.update(
            super(CIIncidentsEdit, self).get_context_data_paginator(
                *args,
                **kwargs
            )
        )
        ret.update({
            'sort_variable_name': self.sort_variable_name,
            'url_query': self.request.GET,
            'sort': self.sort,
            'columns': self.columns,
            'jira_url': JIRA_URL,
            'form': {
                'filters': ReportFilters(self.request.GET),
                'date_range': ReportFiltersDateRange(self.request.GET),
            },
            'possible_title': _('Incidents that could affect this CI'),
            'possible_data': collect(
                self.ci,
                self.get_events,
                up=False,
                exclusive=True,
            ),
        })
        return ret

    def get_events(self, ci):
        return db.CIProblem.objects.filter(
            cis=ci,
            update_date__gte=(
                datetime.datetime.now() -
                settings.POSSIBLE_EVENTS_TIMEDELTA
            ),
        )

    @ralph_permission(perms)
    def get(self, *args, **kwargs):

        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except db.CI.DoesNotExist:
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.data_table_query(
            report_filters(
                cls=db.CIIncident,
                order='-update_date',
                filters=add_filter(self.request.GET, cis=self.ci),
            )
        )
        return super(CIIncidentsEdit, self).get(*args, **kwargs)


class CIIncidentsView(CIIncidentsEdit):

    def get_context_data(self, **kwargs):
        ret = super(CIIncidentsView, self).get_context_data(**kwargs)
        return _update_labels(ret, self.ci)


class Search(BaseCMDBView):
    template_name = 'cmdb/search_ci.html'
    Form = CISearchForm
    cis = []

    def get_context_data(self, **kwargs):
        subsection = ''
        layer = self.request.GET.get('layer')
        type = self.request.GET.get('type')
        if layer:
            subsection += '%s - ' % CILayer.objects.get(id=layer)
        elif type:
            type = CIType.objects.get(pk=type)
            subsection += '%s - ' % type.name
        subsection += 'Search'
        if layer is None:
            sidebar_selected = 'all-cis'
        else:
            select = CILayer.objects.get(id=layer)
            sidebar_selected = slugify(select.name)
        ret = super(Search, self).get_context_data(**kwargs)
        ret.update({
            'table_header': self.table_header,
            'table_body': self.table_body,
            'page': self.page,
            'pages': _get_pages(self.paginator, self.page_number),
            'sort': self.request.GET.get('sort', ''),
            'layer': self.request.GET.get('layer', ''),
            'form': self.form,
            'sidebar_selected': sidebar_selected,
            'subsection': subsection,
        })
        return ret

    def form_initial(self, values):
        return values

    def get_table_header(self, layer, type_):
        DEFAULT_COLS = (
            {'label': 'Type', 'name': 'type', 'sortable': 1},
            {'label': 'Layer', 'name': 'layers', 'sortable': 1},
            {'label': 'Venture', 'name': 'Venture'},
            {'label': 'Service', 'name': 'Service'},
            {'label': 'PCI Scope', 'name': 'pci_scope', 'sortable': 1},
        )
        table_header = (
            {'label': 'Name', 'name': 'name', 'sortable': 1},
            {'label': 'CI UID', 'name': 'uid', 'sortable': 1},
        )
        if type_ == 0:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.APPLICATION.id:
            table_header += (
                {'label': 'Type', 'name': 'type'},
                {'label': 'Layer', 'name': 'layers', 'sortable': 1},
                {'label': 'Venture', 'name': 'Venture'},
                {'label': 'Service', 'name': 'Service'},
                {'label': 'PCI Scope', 'name': 'pci_scope', 'sortable': 1},
            )
        elif type_ == CI_TYPES.DEVICE.id:
            table_header += (
                {'label': 'Parent Device', 'name': 'Parent Device'},
                {'label': 'Network', 'name': 'Network'},
                {'label': 'DC', 'name': 'DC'},
                {'label': 'Venture', 'name': 'Venture'},
                {'label': 'Service', 'name': 'Service'},
                {'label': 'PCI Scope', 'name': 'pci_scope', 'sortable': 1},
            )
        elif type_ == CI_TYPES.PROCEDURE.id:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.VENTURE.id:
            table_header += (
                {'label': 'Parent venture', 'name': 'Parent venture'},
                {'label': 'Child Ventures', 'name': 'Child Ventures'},
                {'label': 'Service', 'name': 'Service'},
                {'label': 'Technical Owner', 'name': 'Technical Owner'},
                {'label': 'Business Owner', 'name': 'Business Owner'},
            )
        elif type_ == CI_TYPES.VENTUREROLE.id:
            table_header += (
                {'label': 'Parent venture', 'name': 'Parent venture'},
                {'label': 'Service', 'name': 'Service'},
                {'label': 'Technical Owner', 'name': 'Technical Owner'},
            )
        elif type_ == CI_TYPES.BUSINESSLINE.id:
            table_header += ({
                'label': 'Services contained',
                'name': 'Services contained',
            },)
        elif type_ == CI_TYPES.SERVICE.id:
            table_header += (
                {'label': 'Contained Venture', 'name': 'Contained Venture'},
                {'label': 'Business Line', 'name': 'Business Line'},
                {'label': 'Technical Owner', 'name': 'Technical Owner'},
                {'label': 'Business Owner', 'name': 'Business Owner'},
            )
        elif type_ == CI_TYPES.NETWORK.id:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.DATACENTER.id:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.NETWORKTERMINATOR.id:
            table_header += DEFAULT_COLS
        table_header += ({'label': 'Operations', 'name': 'Operations'},)
        return table_header

    def get_name(self, i, icon):
        return mark_safe(
            '<a href="./ci/view/%s"> <i class="fugue-icon %s"></i> %s</a>' %
            (escape(i.id), escape(icon), escape(i.name))
        )

    def get_uid(self, i):
        return mark_safe('<a href="./ci/view/%s">%s</a>' % (
            escape(i.id), escape(i.uid)))

    def get_layer(self, i):
        return ', '.join(unicode(x) for x in i.layers.select_related())

    def get_parent_dev(self, i):
        parent = '-'
        try:
            parent = i.content_object.parent
        except AttributeError:
            pass
        return parent

    def get_network(self, i):
        network = '-'
        try:
            networks = i.content_object.ipaddress_set.all()
            network = ', '.join(unicode(x) for x in networks)
        except AttributeError:
            pass
        return network

    def get_dc(self, i):
        dc = '-'
        try:
            dc = i.content_object.dc
        except AttributeError:
            pass
        return dc

    def get_owners(self, i, filter):
        owners = ', '.join(
            "%s %s" % (b.owner.first_name, b.owner.last_name)
            for b in i.ciownership_set.filter(type=filter)
        ),
        return owners[0]

    def get_bl(self, i, relations):
        business_line = '-'
        rel_bl = relations.filter(
            child=i.id, parent__type__id=CI_TYPES.BUSINESSLINE.id
        )
        for bl in rel_bl:
            business_line = ('<a href="%s">%s</a>' % (
                escape(reverse('ci_view', kwargs={'ci_id': bl.parent.id})),
                escape(bl.parent.name),
            ))
        return mark_safe(business_line)

    def get_venture(self, relations, i, child=False):
        venture = []
        if child is False:
            ven = relations.filter(
                child=i.id,
                parent__type__id=CI_TYPES.VENTURE.id
            )
            for v in ven:
                venture.append(
                    '<a href="/cmdb/ci/view/%s">%s</a>' % (
                        escape(v.parent.id), escape(v.parent.name))
                )
        elif child is True:
            ven = relations.filter(
                parent=i.id,
                child__type__id=CI_TYPES.VENTURE.id
            )
            for v in ven:
                venture.append(
                    '<a href="/cmdb/ci/view/%s">%s</a>' % (
                        escape(v.child.id), escape(v.child.name))
                )
        return mark_safe(', '.join(x for x in venture))

    def get_service(self, relations, i):
        services = ''
        servi = relations.filter(
            parent=i.id, child__type__id=CI_TYPES.SERVICE.id
        )
        for s in servi:
            services += '%s, ' % escape(s.child.name)
        return mark_safe(services)

    def get_operations(self, i):
        return mark_safe(
            '<a href="./ci/edit/%s">Edit</a> | '
            '<a href="./ci/view/%s">View</a>',
        ) % (escape(i.id), escape(i.id))

    def get_table_body(self, cis, type_):
        """Return data for table body."""
        table_body = []
        relations = CIRelation.objects.all()
        t_owners = 1
        b_owners = 2
        for i in cis:
            icon = i.icon
            venture = self.get_venture(relations, i)
            service = self.get_service(relations, i)
            DEFAULT_ROWS = [
                {'name': 'name', 'value': self.get_name(i, icon)},
                {'name': 'uid', 'value': self.get_uid(i)},
                {'name': 'type', 'value': i.type.name},
                {'name': 'layer', 'value': self.get_layer(i)},
                {'name': 'layer', 'value': venture},
                {'name': 'service', 'value': service},
                {'name': 'pci_scope', 'value': i.pci_scope},
                {'name': 'operations', 'value': self.get_operations(i)}
            ]
            if type_ is None:
                table_body.append(DEFAULT_ROWS)
            elif type_ == CI_TYPES.APPLICATION:
                table_body.append(DEFAULT_ROWS)
            elif type_ == CI_TYPES.DEVICE:
                row = [
                    {'name': 'name', 'value': self.get_name(i, icon)},
                    {'name': 'uid', 'value': self.get_uid(i)},
                    {'name': 'parent-dev', 'value': self.get_parent_dev(i)},
                    {'name': 'network', 'value': self.get_network(i)},
                    {'name': 'dc', 'value': self.get_dc(i)},
                    {'name': 'venture', 'value': venture},
                    {'name': 'service', 'value': service},
                    {'name': 'pci_scope', 'value': i.pci_scope},
                    {'name': 'operations', 'value': self.get_operations(i)}
                ]
                table_body.append(row)
            elif type_ == CI_TYPES.VENTURE:
                venture_c = self.get_venture(relations, i, child=True)
                b_own = self.get_owners(i, b_owners)
                t_own = self.get_owners(i, t_owners)
                row = [
                    {'name': 'name', 'value': self.get_name(i, icon)},
                    {'name': 'uid', 'value': self.get_uid(i)},
                    {'name': 'venture', 'value': venture},
                    {'name': 'venture-child', 'value': venture_c},
                    {'name': 'service', 'value': service},
                    {'name': 't_owners', 'value': t_own},
                    {'name': 'b_owners', 'value': b_own},
                    {'name': 'operations', 'value': self.get_operations(i)}
                ]
                table_body.append(row)
            elif type_ == CI_TYPES.VENTUREROLE:
                t_own = self.get_owners(i, t_owners)
                row = [
                    {'name': 'name', 'value': self.get_name(i, icon)},
                    {'name': 'uid', 'value': self.get_uid(i)},
                    {'name': 'venture', 'value': venture},
                    {'name': 'service', 'value': service},
                    {'name': 't_owners', 'value': t_own},
                    {'name': 'operations', 'value': self.get_operations(i)}
                ]
                table_body.append(row)
            elif type_ == CI_TYPES.BUSINESSLINE:
                ven = relations.filter(parent=i.id)
                services_contained = ', '.join(
                    '<a href="/cmdb/ci/view/%s">%s</a>' %
                    (v.child.id, v.child.name) for v in ven)
                row = [
                    {'name': 'name', 'value': self.get_name(i, icon)},
                    {'name': 'uid', 'value': self.get_uid(i)},
                    {'name': 'venture', 'value': services_contained},
                    {'name': 'operations', 'value': self.get_operations(i)}
                ]
                table_body.append(row)
            elif type_ == CI_TYPES.SERVICE.id:
                venture_c = self.get_venture(relations, i, child=True)
                b_own = self.get_owners(i, b_owners)
                t_own = self.get_owners(i, t_owners)
                row = [
                    {'name': 'name', 'value': self.get_name(i, icon)},
                    {'name': 'uid', 'value': self.get_uid(i)},
                    {'name': 'venture-child', 'value': venture_c},
                    {'name': 'bl', 'value': self.get_bl(i, relations)},
                    {'name': 't_owners', 'value': t_own},
                    {'name': 'b_owners', 'value': b_own},
                    {'name': 'operations', 'value': self.get_operations(i)}
                ]
                table_body.append(row)
            else:
                table_body.append(DEFAULT_ROWS)
        return table_body

    def get(self, *args, **kwargs):
        values = self.request.GET
        cis = db.CI.objects.all()
        uid = values.get('uid')
        state = values.get('state')
        status = values.get('status')
        type_ = int(values.get('type', 0) or 0)
        layer = values.get('layer')
        parent_id = int(values.get('parent', 0) or 0)
        if uid:
            cis = cis.filter(Q(name__icontains=uid) | Q(uid=uid))
        if state:
            cis = cis.filter(state=state)
        if status:
            cis = cis.filter(status=status)
        if type_:
            cis = cis.filter(type=type_)
        if layer:
            cis = cis.filter(layers=layer)
        if parent_id:
            cis = cis.filter(child__parent__id=parent_id)
        if not values.get('show_inactive', False):
            cis = cis.exclude(state=CI_STATE_TYPES.INACTIVE.id)
        sort = self.request.GET.get('sort', 'name')
        if sort:
            cis = cis.order_by(sort)
        if values.get('top_level'):
            cis = cis.filter(child__parent=None)
        page = self.request.GET.get('page') or 1
        self.page_number = int(page)
        self.paginator = Paginator(cis, ROWS_PER_PAGE)
        try:
            cis = self.paginator.page(page)
        except PageNotAnInteger:
            cis = self.paginator.page(1)
            page = 1
        except EmptyPage:
            cis = self.paginator.page(self.paginator.num_pages)
            page = self.paginator.num_pages
        self.page = cis
        self.table_header = self.get_table_header(layer, type_)
        self.table_body = self.get_table_body(cis, type_),
        form_options = dict(
            label_suffix='',
            initial=self.form_initial(values),
        )
        self.form = self.Form(**form_options)
        return super(Search, self).get(*args, **kwargs)


class Index(BaseCMDBView):
    template_name = 'cmdb/index.html'

    def get_context_data(self, **kwargs):
        ret = super(Index, self).get_context_data(**kwargs)
        return ret


class ViewUnknown(BaseCMDBView):
    template_name = 'cmdb/view_ci_error.html'

    def get_context_data(self, **kwargs):
        ret = super(ViewUnknown, self).get_context_data(**kwargs)
        ret.update({
            'error_message':
            'This Configuration Item cannot be found in the CMDB.'})
        return ret


class Graphs(BaseCMDBView):
    template_name = 'cmdb/graphs.html'
    rows = []
    graph_data = {}

    def get_context_data(self, *args, **kwargs):
        ret = super(Graphs, self).get_context_data(**kwargs)
        form = SearchImpactForm(initial=self.get_initial())
        ret.update(dict(
            form=form,
            rows=self.rows,
            graph_data=self.graph_data,
        ))
        return ret

    def get_initial(self):
        return dict(
            ci=self.request.GET.get('ci'),
        )

    def get(self, *args, **kwargs):
        MAX_RELATIONS_COUNT = 1000
        ci_id = self.request.GET.get('ci')
        self.rows = []
        ci_names = {}
        if ci_id:
            ic = ImpactCalculator(root_ci=CI.objects.get(pk=int(ci_id)))
            search_tree, pre = ic.find_affected_nodes(int(ci_id))
            affected_cis = CI.objects.select_related(
                'content_type', 'type').filter(pk__in=pre)
            nodes = [(ci.id, ci.name, ci.icon) for ci in affected_cis]
            if len(search_tree) > MAX_RELATIONS_COUNT:
                # in case of large relations count, skip generating json data
                # for chart purposes
                self.graph_data = simplejson.dumps(
                    {'overflow': len(search_tree)}
                )
            else:
                ci_names = dict(CI.objects.values_list('id', 'name'))
                relations = [dict(
                    child=item,
                    parent=search_tree.get(item),
                    parent_name=ci_names[item],
                    type=ic.graph.edge_attributes(
                        (search_tree.get(item), item)
                    )[0],
                    child_name=ci_names[search_tree.get(item)]) for item
                    in search_tree.keys() if item and search_tree.get(item)
                ]
                self.graph_data = simplejson.dumps(dict(
                    nodes=nodes,
                    relations=relations,
                ))

            for ci in affected_cis:
                co = ci.content_object
                self.rows.append(dict(
                    icon=ci.icon,
                    ci=ci,
                    venture=getattr(co, 'venture', ''),
                    role=getattr(co, 'role', ''),
                ))

        return super(BaseCMDBView, self).get(*args, **kwargs)


class Cleanup(Search):

    """The view containing various data useful for clean up tasks."""

    template_name = 'cmdb/cleanup.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(Cleanup, self).get_context_data()
        ret['duplicates'] = CI.get_duplicate_names()
        ret['header'] = self.get_table_header(None, 0)
        orphans = CI.objects.filter(parent=None, child=None)
        ret['orphans_table'] = [self.get_table_body(orphans, None)]
        return ret
