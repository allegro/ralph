#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from urlparse import urljoin

from django.db.models import Q
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
from lck.django.common import nested_commit_on_success
from lck.django.filters import slugify
from bob.menu import MenuItem, MenuHeader

from ralph.cmdb.forms import (
    CISearchForm, CIEditForm, CIViewForm, CIRelationEditForm, SearchImpactForm
)
from ralph.cmdb.customfields import EditAttributeFormFactory
from ralph.cmdb.models_ci import (
    CIOwner, CIOwnership, CILayer, CI_TYPES, CI, CIRelation, CI_LAYER
)
import ralph.cmdb.models as db
from ralph.cmdb.graphs import search_tree, ImpactCalculator
from ralph.account.models import Perm
from ralph.ui.views.common import Base, _get_details
from ralph.util.presentation import (
    get_device_icon, get_venture_icon, get_network_icon
)


ROWS_PER_PAGE = 20
SAVE_PRIORITY = 200


def get_icon_for(ci):
    if not ci or not ci.content_object:
        return
    if ci.content_type.name == 'venture':
        return get_venture_icon(ci.content_object)
    elif ci.content_type.name == 'device':
        return get_device_icon(ci.content_object)
    elif ci.content_type.name == 'network':
        return get_network_icon(ci.content_object)
    else:
        return 'wall'


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

    def get_permissions_dict(self):
        has_perm = self.request.user.get_profile().has_perm
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

    def get_sidebar_items(self):
        ci = (
            ('/cmdb/add', 'Add CI', 'fugue-block--plus'),
            ('/cmdb/changes/dashboard', 'Dashboard', 'fugue-dashboard'),
            ('/cmdb/graphs', 'Impact report', 'fugue-dashboard'),
            ('/cmdb/graphs_tree', 'Tree deps.', 'fugue-dashboard'),
            ('/cmdb/changes/dashboard', 'Dashboard', 'fugue-dashboard'),
            ('/cmdb/changes/timeline', 'Timeline View', 'fugue-dashboard'),
            ('/admin/cmdb', 'Admin', 'fugue-toolbox'),
        )

        layers = (
            ('/cmdb/search?layer=1&type=1', 'Applications',
             'fugue-applications-blue'),
            ('/cmdb/search?layer=2&top_level=1', 'Databases',
             'fugue-database'),
            ('/cmdb/search?layer=3&top_level=1', 'Documentation/Procedures',
             'fugue-blue-documents'),
            ('/cmdb/search?layer=4&top_level=1',
             'Organization Unit/Support Group',
             'fugue-books-brown'),
            ('/cmdb/search?layer=5&type=2', 'Hardware',
             'fugue-processor'),
            ('/cmdb/search?layer=6&type=8', 'Network',
             'fugue-network-ip'),
            ('/cmdb/search?layer=7&type=7', 'Services',
             'fugue-disc-share'),
            ('/cmdb/search?layer=8&type=5', 'Roles',
             'fugue-computer-network'),
            ('/cmdb/search', 'All Cis (all layers)', 'fugue-magnifier'),
        )
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
            ('/cmdb/changes/changes?type=5', 'Status Office events',
                'fugue-plug'),
            ('/cmdb/changes/incidents', 'Incidents',
                'fugue-question'),
            ('/cmdb/changes/problems', 'Problems',
                'fugue-bomb')
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
            ) for t in events]
        )
        return sidebar_items

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        ret.update(self.get_permissions_dict())
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
    return ', '.join(form.errors['__all__']) or 'Correct the errors.' if form.errors else ''


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
        if not self.get_permissions_dict().get(
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
        if not self.get_permissions_dict().get(
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
                model.owners.clear()
                model.layers.clear()
                layers = self.form.data.getlist('base-layers')
                for layer in layers:
                    model.layers.add(CILayer.objects.get(pk=int(layer[0])))

                owners_t = self.form.data.getlist('base-technical_owners')
                for owner in owners_t:
                    own = CIOwnership(ci=model,
                                      owner=CIOwner.objects.get(pk=owner[0]),
                                      type=1,)
                    own.save()
                owners_b = self.form.data.getlist('base-business_owners')
                for owner in owners_b:
                    own = CIOwnership(ci=model,
                                      owner=CIOwner.objects.get(pk=owner[0]),
                                      type=2,)
                    own.save()
                messages.success(self.request, _("Changes saved."))
                return HttpResponseRedirect('/cmdb/ci/edit/' + unicode(model.id))
            else:
                messages.error(self.request, _("Correct the errors."))

        return super(Add, self).get(*args, **kwargs)


class LastChanges(BaseCMDBView):
    template_name = 'cmdb/search_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(LastChanges, self).get_context_data(**kwargs)
        ret.update({
            'last_changes': self.last_changes,
            'jira_url': urljoin(settings.ISSUETRACKERS['default']['URL'], 'browse'),
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


class Edit(BaseCMDBView):
    template_name = 'cmdb/edit_ci.html'
    Form = CIEditForm
    form_attributes_options = dict(label_suffix='', prefix='attr')
    form_options = dict(label_suffix='', prefix='base')

    def get_first_parent_venture_name(self, ci_id):
        cis = db.CI.objects.filter(
            relations__parent__child=ci_id,
            relations__parent__parent__type=db.CI_TYPES.VENTUREROLE.id).all()
        if cis:
            return cis[0].name

    def generate_breadcrumb(self):
        if getattr(self, 'ci'):
            parent = self.ci.id
        else:
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

    def get_messages(self):
        days = datetime.timedelta(days=7)
        last_week_puppet_errors = db.CIChangePuppet.objects.filter(
            ci=self.ci,
            time__range=(
                datetime.datetime.now(), datetime.datetime.now() - days)
        ).count()

        incidents = db.CIIncident.objects.filter(
            ci=self.ci,
        ).count()

        problems = db.CIProblem.objects.filter(
            ci=self.ci,
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

    def get_context_data(self, **kwargs):
        ret = super(Edit, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'form_attributes': self.form_attributes,
            'ci': self.ci,
            'ci_id': self.ci.id,
            'uid': self.ci.uid,
            'label': 'Edit CI: {} (uid: {})'.format(self.ci.name, self.ci.uid),
            'relations_contains': self.relations_contains,
            'relations_requires': self.relations_requires,
            'relations_isrequired': self.relations_isrequired,
            'relations_parts': self.relations_parts,
            'relations_hasrole': self.relations_hasrole,
            'relations_isrole': self.relations_isrole,
            'puppet_reports': self.puppet_reports,
            'git_changes': self.git_changes,
            'device_attributes_changes': self.device_attributes_changes,
            'ci_attributes_changes': self.ci_attributes_changes,
            'problems': self.problems,
            'incidents': self.incidents,
            'zabbix_triggers': self.zabbix_triggers,
            'service_name': self.service_name,
            'so_events': self.so_events,
            'cmdb_messages': self.get_messages(),
            'show_in_ralph': self.show_in_ralph,
            'ralph_ci_link': self.ralph_ci_link,
            'subsection': 'Edit - %s' % self.ci.name,
        })
        return ret

    def custom_form_initial(self, ci):
        data = dict()
        objs = db.CIAttributeValue.objects.filter(ci=ci)
        for obj in objs:
            field_type = obj.attribute.attribute_type
            if field_type == db.CI_ATTRIBUTE_TYPES.INTEGER.id:
                field_type = 'integer'
                value = obj.value_integer.value
            elif field_type == db.CI_ATTRIBUTE_TYPES.STRING.id:
                field_type = 'string'
                value = obj.value_string.value
            elif field_type == db.CI_ATTRIBUTE_TYPES.FLOAT.id:
                field_type = 'float'
                value = obj.value_float.value
            elif field_type == db.CI_ATTRIBUTE_TYPES.DATE.id:
                field_type = 'date'
                value = obj.value_date.value
            elif field_type == db.CI_ATTRIBUTE_TYPES.CHOICE.id:
                field_type = 'choice'
                value = obj.value_choice.value
            data['attribute_%s_%s' % (field_type, obj.attribute_id)] = value
        return data

    def form_initial(self, ci):
        data = dict(
            technical_owner=', '.join(ci.get_technical_owners()),
            ci=self.ci,
        )
        return data

    def check_perm(self):
        if not self.get_permissions_dict().get(
                'edit_configuration_item_info_generic_perm', False):
            return HttpResponseForbidden()

    def calculate_relations(self, ci_id):
        self.relations_contains = [
            (x, x.child, get_icon_for(x.child))
            for x in db.CIRelation.objects.filter(
                parent=ci_id, type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_parts = [
            (x, x.parent, get_icon_for(x.parent))
            for x in db.CIRelation.objects.filter(
                child=ci_id,
                type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_requires = [
            (x, x.child, get_icon_for(x.parent))
            for x in db.CIRelation.objects.filter(
                parent=ci_id, type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_isrequired = [
            (x, x.parent, get_icon_for(x.parent))
            for x in db.CIRelation.objects.filter(
                child=ci_id, type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_hasrole = [
            (x, x.child, get_icon_for(x.parent))
            for x in db.CIRelation.objects.filter(
                parent=ci_id, type=db.CI_RELATION_TYPES.HASROLE.id)
        ]
        self.relations_isrole = [
            (x, x.parent, get_icon_for(x.parent))
            for x in db.CIRelation.objects.filter(
                child=ci_id, type=db.CI_RELATION_TYPES.HASROLE.id)
        ]

    def get_ci_id(self):
        """ 2 types of id can land here. """
        ci_id = self.kwargs.get('ci_id')
        if ci_id.find('-') >= 0:
            ci = db.CI.objects.get(uid=ci_id)
            return ci.id
        else:
            return self.kwargs.get('ci_id', None)

    def get(self, *args, **kwargs):
        if self.check_perm():
            return self.check_perm()
        self.initialize_vars()
        try:
            ci_id = self.get_ci_id()
        except:
            # editing/viewing Ci which doesn's exists.
            return HttpResponseRedirect('/cmdb/ci/jira_ci_unknown')
        if ci_id:
            self.ci = get_object_or_404(db.CI, id=ci_id)
            # preview only for devices
            if (self.ci.content_object and
                    self.ci.content_type.name == 'device'):
                self.show_in_ralph = True
                self.ralph_ci_link = ("/ui/search/info/%d" %
                                      self.ci.content_object.id)
            self.service_name = self.get_first_parent_venture_name(ci_id)
            self.problems = db.CIProblem.objects.filter(
                ci=self.ci).order_by('-time').all()
            self.incidents = db.CIIncident.objects.filter(
                ci=self.ci).order_by('-time').all()
            self.git_changes = [
                x.content_object for x in db.CIChange.objects.filter(
                    ci=self.ci, type=db.CI_CHANGE_TYPES.CONF_GIT.id)]
            self.device_attributes_changes = [
                x.content_object for x in db.CIChange.objects.filter(
                    ci=self.ci, type=db.CI_CHANGE_TYPES.DEVICE.id)]
            self.ci_attributes_changes = [
                x.content_object for x in db.CIChange.objects.filter(
                    ci=self.ci, type=db.CI_CHANGE_TYPES.CI.id).order_by('time')
            ]
            reps = db.CIChangePuppet.objects.filter(ci=self.ci).all()
            for report in reps:
                puppet_logs = db.PuppetLog.objects.filter(
                    cichange=report).all()
                self.puppet_reports.append(
                    dict(report=report, logs=puppet_logs)
                )
            self.zabbix_triggers = db.CIChangeZabbixTrigger.objects.filter(
                ci=self.ci).order_by('-lastchange')
            self.so_events = db.CIChange.objects.filter(
                type=db.CI_CHANGE_TYPES.STATUSOFFICE.id,
                ci=self.ci).all()
            self.calculate_relations(ci_id)
            self.form_options['instance'] = self.ci
            self.form_options['initial'] = self.form_initial(self.ci)
            self.form_attributes_options['initial'] = self.custom_form_initial(
                self.ci)
            self.form_attributes = EditAttributeFormFactory(
                ci=self.ci).factory(
                    **self.form_attributes_options)
        self.form = self.Form(**self.form_options)
        return super(Edit, self).get(*args, **kwargs)

    def initialize_vars(self):
        self.form_attributes = {}
        self.service_name = ''
        self.relations_contains = []
        self.relations_requires = []
        self.relations_parts = []
        self.relations_hasrole = []
        self.relations_isrole = []
        self.relations_isrequired = []

        self.puppet_reports = []
        self.git_changes = []
        self.zabbix_triggers = []
        self.ci_attributes_changes = []
        self.device_attributes_changes = []
        self.form = None
        self.ci = None

        self.relations_contains = []
        self.relations_requires = []
        self.relations_parts = []
        self.relations_hasrole = []
        self.relations_isrole = []
        self.relations_isrequired = []
        self.puppet_reports = []
        self.git_changes = []
        self.device_attributes_changes = []
        self.zabbix_triggers = []
        self.so_events = []
        self.problems = []
        self.incidents = []
        self.show_in_ralph = False
        self.ralph_ci_link = ""

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
            self.form_attributes = EditAttributeFormFactory(
                ci=self.ci).factory(
                    self.request.POST,
                    **self.form_attributes_options
                )
            if self.form.is_valid() and self.form_attributes.is_valid():
                model = self.form.save(commit=False)
                model.id = self.ci.id
                model.owners.clear()
                model.layers.clear()
                layers = self.form_attributes.data.getlist('base-layers')
                for layer in layers:
                    model.layers.add(CILayer.objects.get(pk=int(layer)))
                owners_t = self.form_attributes.data.getlist(
                    'base-technical_owners')
                for owner in owners_t:
                    own = CIOwnership(
                        ci=model,
                        owner=CIOwner.objects.get(pk=owner),
                        type=1,)
                    own.save()
                owners_b = self.form_attributes.data.getlist(
                    'base-business_owners')
                for owner in owners_b:
                    own = CIOwnership(
                        ci=model, owner=CIOwner.objects.get(pk=owner),
                        type=2,)
                    own.save()
                model.save(user=self.request.user)
                self.form_attributes.ci = model
                self.form_attributes.save()
                messages.success(self.request, "Changes saved.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Correct the errors.")
        return super(Edit, self).get(*args, **kwargs)


class View(Edit):
    template_name = 'cmdb/view_ci.html'
    Form = CIViewForm

    def get_context_data(self, **kwargs):
        ret = super(View, self).get_context_data(**kwargs)
        ret.update({
            'label': 'View CI: {} (uid: {})'.format(self.ci.name, self.ci.uid),
            'subsection': 'Info - %s' % self.ci.name
        })
        return ret

    def check_perm(self):
        if not self.get_permissions_dict().get(
                'read_configuration_item_info_generic_perm', False):
            return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """ Overwrite parent class post """
        return HttpResponseForbidden()


class ViewIframe(View):
    template_name = 'cmdb/view_ci_iframe.html'

    def get_context_data(self, **kwargs):
        ret = super(ViewIframe, self).get_context_data(**kwargs)
        ret.update({'target': '_blank'})
        return ret


class ViewJira(ViewIframe):
    template_name = 'cmdb/view_ci_iframe.html'

    def get_ci_id(self):
        ci_uid = self.kwargs.get('ci_uid', None)
        ci = db.CI.objects.get(uid=ci_uid)
        #raise 404 in case of missing CI
        return ci.id

    def get_context_data(self, **kwargs):
        ret = super(ViewJira, self).get_context_data(**kwargs)
        ret.update({'span_number': '4'})  # height of screen
        return ret


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
            type = CI_TYPES.NameFromID(int(type))
            subsection += '%s - ' % CI_TYPES.DescFromName(type)
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
            'type': self.request.GET.get('type', ''),
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
            {'label': 'Layer', 'name': 'layer', 'sortable': 0},
            {'label': 'Venture', 'name': 'Venture', 'sortable': 0},
            {'label': 'Service', 'name': 'Service', 'sortable': 0},
            {'label': 'PCI Scope', 'name': 'pci', 'sortable': 0},
        )
        table_header = (
            {'label': 'Name', 'name': 'uid', 'sortable': 1},
            {'label': 'CI UID', 'name': 'type', 'sortable': 0},
        )
        if type_ is None:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.APPLICATION.id:
            table_header += (
                {'label': 'Type', 'name': 'type', 'sortable': 1},
                {'label': 'Layer', 'name': 'layer', 'sortable': 0},
                {'label': 'Venture', 'name': 'Venture', 'sortable': 0},
                {'label': 'Service', 'name': 'Service', 'sortable': 0},
                {'label': 'PCI Scope', 'name': 'pci', 'sortable': 0},
            )
        elif type_ == CI_TYPES.DEVICE.id:
            table_header += (
                {'label': 'Parent Device', 'name': 'Parent Device',
                 'sortable': 1},
                {'label': 'Network', 'name': 'Network', 'sortable': 0},
                {'label': 'DC', 'name': 'DC', 'sortable': 0},
                {'label': 'Venture', 'name': 'Venture', 'sortable': 0},
                {'label': 'Service', 'name': 'Service', 'sortable': 0},
                {'label': 'PPCI Scope', 'name': 'PPCI Scope', 'sortable': 0},
            )
        elif type_ == CI_TYPES.PROCEDURE.id:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.VENTURE.id:
            table_header += (
                {'label': 'Parent venture', 'name': 'Parent venture',
                 'sortable': 1},
                {'label': 'Child Ventures', 'name': 'Child Ventures',
                 'sortable': 1},
                {'label': 'Service', 'name': 'Service', 'sortable': 1},
                {'label': 'Technical Owner', 'name': 'Technical Owner',
                 'sortable': 1},
                {'label': 'Business Owner', 'name': 'Business Owner',
                 'sortable': 1},
            )
        elif type_ == CI_TYPES.VENTUREROLE.id:
            table_header += (
                {'label': 'Parent venture', 'name': 'Parent venture',
                 'sortable': 1},
                {'label': 'Service', 'name': 'Service', 'sortable': 1},
                {'label': 'Technical Owner', 'name': 'Technical Owner',
                 'sortable': 1},
            )
        elif type_ == CI_TYPES.BUSINESSLINE.id:
            table_header += (
                {'label': 'Services contained',
                 'name': 'Services contained', 'sortable': 0},
            )
        elif type_ == CI_TYPES.SERVICE.id:
            table_header += (
                {'label': 'Contained Venture',
                 'name': 'Contained Venture', 'sortable': 1},
                {'label': 'Business Line', 'name': 'Business Line',
                 'sortable': 0},
                {'label': 'Technical Owner', 'name': 'Technical Owner',
                 'sortable': 0},
                {'label': 'Business Owner', 'name': 'Business Owner',
                 'sortable': 0},
            )
        elif type_ == CI_TYPES.NETWORK.id:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.DATACENTER.id:
            table_header += DEFAULT_COLS
        elif type_ == CI_TYPES.NETWORKTERMINATOR.id:
            table_header += DEFAULT_COLS
        table_header += (
            {'label': 'Operations', 'name': 'Operations', 'sortable': 0},
        )
        return table_header

    def get_name(self, i, icon):
        return mark_safe('<a href="./ci/view/%s"> <i class="fugue-icon %s">'
                         '</i> %s</a>' % (
            escape(i.id), escape(icon), escape(i.name))
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
        owners = ', '.join("%s %s" % (b.owner.first_name, b.owner.last_name)
            for b in i.ciownership_set.filter(type=filter)),
        return owners[0]

    def get_bl(self, i, relations):
        business_line = '-'
        rel_bl = relations.filter(
            child=i.id, parent__type__id=CI_TYPES.BUSINESSLINE.id
        )
        for bl in rel_bl:
            business_line = ('<a href="%s">%s</a>' % (
                escape(bl.parent.id), escape(bl.parent.name))
            )
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
        return mark_safe('<a href="./ci/edit/%s">Edit</a> | '
                '<a href="./ci/view/%s">View</a>') % (
                    escape(i.id), escape(i.id)
                )

    def get(self, *args, **kwargs):
        values = self.request.GET
        cis = db.CI.objects.all()
        uid = values.get('uid')
        state = values.get('state')
        status = values.get('status')
        type_ = int(values.get('type', 0) or 0)
        layer = values.get('layer')
        parent_id = int(values.get('parent', 0) or 0)
        if values:
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
        table_body = []
        relations = CIRelation.objects.all()
        t_owners = 1
        b_owners = 2
        for i in cis:
            icon = get_icon_for(i)
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
                b_own = self.get_owners(i, b_owners)
                t_own = self.get_owners(i, t_owners)
                row = [
                    {'name': 'name', 'value': self.get_name(i, icon)},
                    {'name': 'uid', 'value': self.get_uid(i)},
                    {'name': 'venture-child', 'value': venture},
                    {'name': 'bl', 'value': self.get_bl(i, relations)},
                    {'name': 't_owners', 'value': t_own},
                    {'name': 'b_owners', 'value': b_own},
                    {'name': 'operations', 'value': self.get_operations(i)}
                ]
                table_body.append(row)
            else:
                table_body.append(DEFAULT_ROWS)
        self.table_header = self.get_table_header(layer, type_)
        self.table_body = table_body,
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


class CMDB(View):
    template_name = 'cmdb/view_ci_ralph.html'
    read_perm = Perm.read_configuration_item_info_generic

    def get_ci_id(self, *args, **kwargs):
        device_id = self.kwargs.get('device')
        try:
            return CI.objects.get(
                type=CI_TYPES.DEVICE.id,
                object_id=device_id
            ).id
        except CI.objects.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        ret = super(View, self).get_context_data(**kwargs)
        ret.update({
            'ci': self.ci,
            'label': 'View CI: {} (uid: {})'.format(self.ci.name, self.ci.uid),
            'url_query': self.request.GET,
            'components': _get_details(
                self.ci.content_object, purchase_only=False
            )
        })
        return ret


class GraphsTree(BaseCMDBView):
    template_name = 'cmdb/graphs_tree.html'

    @staticmethod
    def get_ajax(request):
        root = CI.objects.get(pk=request.GET.get('ci_id'))
        response_dict = search_tree({}, root)
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/json',
        )

    def get_initial(self):
        return dict(
            ci=self.request.GET.get('ci'),
        )

    def get_context_data(self, *args, **kwargs):
        ret = super(GraphsTree, self).get_context_data(**kwargs)
        form = SearchImpactForm(initial=self.get_initial())
        ret.update(dict(
            form=form,
        ))
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
            graph_data=simplejson.dumps(self.graph_data),
        ))
        return ret

    def get_initial(self):
        return dict(
            ci=self.request.GET.get('ci'),
        )

    def get(self, *args, **kwargs):
        ci_id = self.request.GET.get('ci')
        self.rows = []
        if ci_id:
            ci_names = dict([(x.id, x.name) for x in CI.objects.all()])
            i = ImpactCalculator()
            st, pre = i.find_affected_nodes(int(ci_id))
            nodes = [(
                key, ci_names[key],
                get_icon_for(CI.objects.get(pk=key))) for key in st.keys()]
            relations = [dict(
                child=x,
                parent=st.get(x),
                parent_name=ci_names[x],
                type=i.graph.edge_attributes((st.get(x), x))[0],
                child_name=ci_names[st.get(x)])
                for x in st.keys() if x and st.get(x)]
            self.graph_data = dict(
                nodes=nodes, relations=relations)
            self.rows = [dict(
                icon=get_icon_for(CI.objects.get(pk=x)),
                ci=CI.objects.get(pk=x)) for x in pre]
        return super(BaseCMDBView, self).get(*args, **kwargs)


