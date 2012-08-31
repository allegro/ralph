#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.cmdb.forms import CISearchForm, CIEditForm, CIViewForm, CIRelationEditForm
from ralph.cmdb.customfields import EditAttributeFormFactory
from ralph.account.models import Perm
from ralph.ui.views.common import Base
from ralph.util.presentation import get_device_icon, get_venture_icon, get_network_icon
import ralph.cmdb.models  as db
from bob.menu import MenuItem, MenuHeader


ROWS_PER_PAGE=20
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


class BaseCMDBView(Base):
    template_name = 'nope.html'
    Form = CIRelationEditForm

    def generate_breadcrumb(self):
        parent = self.request.GET.get('parent', '')
        if not parent:
            return []
        list = []
        counter = 0
        while parent and counter<100:
            ci = db.CI.objects.filter(id=parent).all()[0]
            list.insert(0, ci)
            try:
                parent = db.CI.objects.filter(parent__child=parent).all()[0].id
            except:
                parent = None
            if parent == ci.id:
                parent = None
            counter+=1
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
            ret.update({ perm + '_perm': has_perm(getattr(Perm, perm))})
        return ret

    def get_sidebar_items(self):
        ci = (
                ('/cmdb/search', 'All Cis', 'fugue-magnifier'),
                ('/cmdb/search?layer=7&top_level=1', 'Services', 'fugue-disc-share'),
                ('/cmdb/add', 'Add CI', 'fugue-block--plus'),
                ('/cmdb/changes/dashboard', 'Dashboard', 'fugue-dashboard'),
                ('/cmdb/changes/timeline', 'Timeline View', 'fugue-dashboard'),
                ('/admin/cmdb', 'Admin', 'fugue-toolbox'),
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
                ('/cmdb/changes/changes', 'All Events',
                    'fugue-arrow' ),
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
                ) for t in events ]
        )
        return sidebar_items

    def get_context_data(self, **kwargs):
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
        })
        return ret

def _get_pages(paginator, page):
    pages = paginator.page_range[max(0, page - 4):min(paginator.num_pages, page + 3)]
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
        if not  self.get_permissions_dict().get('edit_configuration_item_relations_perm',
                False):
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
        if not  self.get_permissions_dict().get('edit_configuration_item_relations_perm',
                False):
            return HttpResponseForbidden()
        self.rel_parent = self.request.GET.get('rel_parent')
        self.rel_child = self.request.GET.get('rel_child')
        ci_id = kwargs.get('ci_id')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.relations_parent = [
                x.child for x in  db.CIRelation.objects.filter(parent=ci_id)]
        self.relations_child = [
                x.parent for x in db.CIRelation.objects.filter(child=ci_id)]
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
        self.relations_child= db.CIRelation.objects.filter(
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
                return HttpResponseRedirect('/cmdb/ci/edit/'+str(model.id))
            else:
                messages.error(self.request, _("Correct the errors."))
        return super(Add, self).get(*args, **kwargs)


class LastChanges(BaseCMDBView):
    template_name = 'cmdb/search_changes.html'

    def get_context_data(self, **kwargs):
        ret = super(LastChanges, self).get_context_data(**kwargs)
        ret.update({
            'last_changes': self.last_changes,
        })
        return ret

    def get_last_changes(self, ci):
        from ralph.cmdb.integration.jira import Jira
        params = dict(jql='DB\\ CI="%s"' % self.ci_uid)
        xxx=Jira().find_issues(params)
        items_list = []
        for i in xxx.get('issues'):
            f = i.get('fields')
            items_list.append(dict(
                key = i.get('key'),
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
    form_attributes_options = dict(
                    label_suffix='',
                    prefix='attr',
    )
    form_options = dict(
                label_suffix='',
                prefix='base',
    )

    def get_first_parent_venture_name(self, ci_id):
        cis = db.CI.objects.filter(
                relations__parent__child=ci_id,
                relations__parent__parent__type=db.CI_TYPES.VENTUREROLE.id).all()
        if cis:
            return cis[0].name

    def generate_breadcrumb(self):
        if getattr(self, 'ci'):
            ci=self.ci
            parent = ci.id
        else:
            return []
        list = []
        counter = 0
        while parent and counter<100:
            ci = db.CI.objects.filter(id=parent).all()[0]
            list.insert(0, ci)
            try:
                parent = db.CI.objects.filter(parent__child=parent).all()[0].id
            except:
                parent = None
            if parent == ci.id:
                parent = None
            counter+=1
        return list

    def get_messages(self):
        days=datetime.timedelta(days=7)
        last_week_puppet_errors = db.CIChangePuppet.objects.filter(
                ci=self.ci,
                time__range=(datetime.datetime.now(), datetime.datetime.now() - days)
        ).count()

        incidents = db.CIIncident.objects.filter(
                ci=self.ci,
        ).count()

        problems = db.CIProblem.objects.filter(
                ci=self.ci,
        ).count()
        messages=[]
        if last_week_puppet_errors:
            messages.append(dict(
                message="Puppet reported %d errors since last week." % ( last_week_puppet_errors ),
                title='Warning',
                type='warning',
            ))
        if incidents:
            messages.append(dict(
                message="This CI has %d incidents." % ( incidents ),
                title='Be carefull.',
                type='error',
            ))
        if problems:
            messages.append(dict(
                message="This CI has %d problems." % ( problems ),
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
            'label': 'Edit CI - ' + self.ci.uid,
            'relations_contains': self.relations_contains,
            'relations_requires': self.relations_requires,
            'relations_isrequired': self.relations_isrequired,
            'relations_parts': self.relations_parts,
            'relations_hasrole': self.relations_hasrole,
            'relations_isrole': self.relations_isrole,
            'puppet_reports': self.puppet_reports,
            'git_changes': self.git_changes,
            'device_attributes_changes': self.device_attributes_changes,
            'problems': self.problems,
            'incidents': self.incidents,
            'zabbix_triggers': self.zabbix_triggers,
            'service_name': self.service_name,
            'so_events': self.so_events,
            'cmdb_messages': self.get_messages(),
            'show_in_ralph': self.show_in_ralph,
            'ralph_ci_link': self.ralph_ci_link,

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
                technical_owner = ', '.join(ci.get_technical_owners()),
                ci=self.ci,
        )
        return data

    def check_perm(self):
        if not  self.get_permissions_dict().get('edit_configuration_item_info_generic_perm', False):
            return HttpResponseForbidden()

    def calculate_relations(self, ci_id):
        self.relations_contains = [ (x, x.child, get_icon_for(x.child))
                    for x in db.CIRelation.objects.filter(
                    parent=ci_id, type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_parts = [(x, x.parent, get_icon_for(x.parent))
                for x in db.CIRelation.objects.filter( child=ci_id,
                type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_requires = [(x, x.child, get_icon_for(x.parent))
                for x in db.CIRelation.objects.filter( parent=ci_id,
                type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_isrequired = [(x, x.parent, get_icon_for(x.parent))
                for x in db.CIRelation.objects.filter( child=ci_id,
                type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_hasrole = [(x, x.child, get_icon_for(x.parent))
                for x in db.CIRelation.objects.filter( parent=ci_id,
                type=db.CI_RELATION_TYPES.HASROLE.id)
        ]
        self.relations_isrole = [(x, x.parent, get_icon_for(x.parent))
                for x in db.CIRelation.objects.filter( child=ci_id,
                type=db.CI_RELATION_TYPES.HASROLE.id)
        ]

    def get_ci_id(self):
        """ 2 types of id can land here. """
        ci_id = self.kwargs.get('ci_id')
        if ci_id.find('-')>=0:
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
            if self.ci.content_object and self.ci.content_type.name == 'device':
                self.show_in_ralph = True
                self.ralph_ci_link = "/ui/search/info/%d" % self.ci.content_object.id
            self.service_name = self.get_first_parent_venture_name(ci_id)
            self.problems = db.CIProblem.objects.filter(
                    ci=self.ci).order_by('-time').all()
            self.incidents = db.CIIncident.objects.filter(
                    ci=self.ci).order_by('-time').all()
            self.git_changes  = [ x.content_object
                    for x in db.CIChange.objects.filter(
                        ci=self.ci, type=db.CI_CHANGE_TYPES.CONF_GIT.id)]
            self.device_attributes_changes  = [ x.content_object
                    for x in db.CIChange.objects.filter(
                        ci=self.ci, type=db.CI_CHANGE_TYPES.DEVICE.id) ]
            reps = db.CIChangePuppet.objects.filter(ci=self.ci).all()
            for report in reps:
                puppet_logs = db.PuppetLog.objects.filter(cichange=report).all()
                self.puppet_reports.append(dict(report=report, logs=puppet_logs))
            self.zabbix_triggers = db.CIChangeZabbixTrigger.objects.filter(
                    ci=self.ci).order_by('-lastchange')
            self.so_events = db.CIChange.objects.filter(
                    type=db.CI_CHANGE_TYPES.STATUSOFFICE.id,
                    ci=self.ci).all()
            self.calculate_relations(ci_id)
            self.form_options['instance'] = self.ci
            self.form_options['initial'] = self.form_initial( self.ci)
            self.form_attributes_options['initial'] = self.custom_form_initial( self.ci)
            self.form_attributes = EditAttributeFormFactory(ci=self.ci).factory(
                    **self.form_attributes_options
            )
        self.form = self.Form(**self.form_options)
        return super(Edit, self).get(*args, **kwargs)

    def initialize_vars(self):
        self.form_attributes = {}
        self.service_name = ''
        self.relations_contains = []
        self.relations_requires= []
        self.relations_parts= []
        self.relations_hasrole= []
        self.relations_isrole= []
        self.relations_isrequired = []

        self.puppet_reports  = []
        self.git_changes = []
        self.zabbix_triggers = []
        self.device_attributes_changes = []
        self.form = None
        self.ci = None

        self.relations_contains = []
        self.relations_requires= []
        self.relations_parts = []
        self.relations_hasrole = []
        self.relations_isrole = []
        self.relations_isrequired = []
        self.puppet_reports  = []
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
            if self.Form:
                self.form = self.Form(self.request.POST, **self.form_options)
                self.form_attributes = EditAttributeFormFactory(
                        ci=self.ci).factory(
                                self.request.POST,
                                **self.form_attributes_options
                        )
                if self.form.is_valid() and self.form_attributes.is_valid():
                    self.form.data['base-id'] = self.ci.id
                    model = self.form.save(commit=False)
                    model.uid = self.ci.uid
                    model.save(user=self.request.user)
                    self.form_attributes.ci = model
                    model_attributes = self.form_attributes.save()
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
            'label': 'View CI:  ' + self.ci.name
        })
        return ret

    def check_perm(self):
        if not  self.get_permissions_dict().get(
                'read_configuration_item_info_generic_perm', False):
            return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """ Overwrite parent class post """
        return HttpResponseForbidden()


class ViewIframe(View):
    template_name = 'cmdb/view_ci_iframe.html'

    def get_context_data(self, **kwargs):
        ret = super(ViewIframe, self).get_context_data(**kwargs)
        ret.update({'target': '_blank' })
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
        ret.update({'span_number': '4' }) #heigh of screen
        return ret


class Search(BaseCMDBView):
    template_name = 'cmdb/search_ci.html'
    Form = CISearchForm
    cis = []
    def get_context_data(self, **kwargs):
        ret = super(Search, self).get_context_data(**kwargs)
        ret.update({
            'rows': self.rows,
            'page': self.page,
            'pages': _get_pages(self.paginator, self.page_number),
            'sort': self.request.GET.get('sort', ''),
            'form': self.form,
        })
        return ret

    def form_initial(self, values):
        return values;

    def get(self, *args, **kwargs):
        values = self.request.GET
        cis = db.CI.objects.all()
        uid = values.get('uid')
        state = values.get('state')
        status = values.get('status')
        type_ = values.get('type')
        layer = values.get('layer')
        parent_id = int(values.get('parent', 0) or 0)
        if values:
            if uid:
                cis = cis.filter(Q(name__icontains=uid)
                        | Q(uid=uid))
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
            page=1
        except EmptyPage:
            cis = self.paginator.page(self.paginator.num_pages)
            page = self.paginator.num_pages
        self.page = cis
        rows = []
        for i in cis:
            icon = get_icon_for(i)
            rows.append({
                'coun': i.relations.count(),
                'uid': i.uid,
                'name': i.name,
                'ci_type': i.type.name,
                'id': i.id,
                'icon': icon,
                'venture': '',
                'layers': ', '.join(unicode(x) for x in i.layers.select_related()),
                'state': i.get_state_display(),
                'state_id': i.state,
                'status': i.get_status_display(),
            })
        self.rows = rows
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
        ret.update({'error_message':
            'This Configuration Item cannot be found in the CMDB.' })
        return ret

