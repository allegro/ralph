#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from ralph.cmdb.forms import CISearchForm, CIEditForm, CIViewForm, CIRelationEditForm
import ralph.cmdb.models  as db
from ralph.cmdb.customfields import EditAttributeFormFactory
from ralph.account.models import Perm
from django.http import HttpResponseForbidden
from ralph.cmdb.integration import zabbix
from ralph.ui.views.common import Base

import datetime

from ralph.util.presentation import get_device_icon, get_venture_icon, get_network_icon
from ralph.ui.views.common import Info

ROWS_PER_PAGE=20
SAVE_PRIORITY = 200

from django import template
register = template.Library()

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
        parent = self.request.GET.get('parent','')
        if not parent:
            return []
        list = []

        counter = 0
        while parent and counter<100:
            ci = db.CI.objects.filter(id=parent).all()[0]
            list.insert(0,ci)
            try:
                parent = db.CI.objects.filter(parent__child=parent).all()[0].id
            except:
                parent = None

            if parent == ci.id:
                parent = None
            counter+=1
        return list

    def get_permissions(self):
        has_perm = self.request.user.get_profile().has_perm
        ci_perms = ['create_configuration_item',
                'edit_configuration_item_info_generic',
                'edit_configuration_item_relations',
                'read_configuration_item_info_generic',
                'read_configuration_item_info_puppet',
                'read_configuration_item_info_git',
                'read_configuration_item_info_jira',
        ]
        ret = {}
        for perm in ci_perms:
            ret.update({ perm + '_perm' : has_perm(getattr(Perm, perm))})
        # layout
        ret.update({
            'read_dc_structure_perm': has_perm(Perm.read_dc_structure),
            'read_device_info_management_perm': has_perm(Perm.read_device_info_management),
            'edit_device_info_financial_perm': has_perm(Perm.edit_device_info_financial),
            'read_network_structure_perm': has_perm(Perm.read_network_structure),
        })
        return ret

    def get_context_data(self, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        ret.update(self.get_permissions())
        ret.update({'breadcrumbs' : self.generate_breadcrumb()})
        ret.update({ 'url_query': self.request.GET, })
        ret.update({'span_number' : '6' }) #high of screen
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
            'form' : self.form,
            'url_query': self.request.GET,
        })
        return ret

    def get(self, *args, **kwargs):
        if not  self.get_permissions().get('edit_configuration_item_relations_perm',False):
            return HttpResponseForbidden()
        rel_id = kwargs.get('relation_id')
        rel = get_object_or_404(db.CIRelation, id=rel_id)
        self.form_options['instance'] = rel
        self.form = self.Form(**self.form_options)
        self.rel_parent = rel.parent
        self.rel_child= rel.child
        self.rel_type= rel.type
        self.rel = rel
        return super(EditRelation, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = None
        self.rel = None
        rel_id = kwargs.get('relation_id')
        rel = get_object_or_404(db.CIRelation, id=rel_id)
        self.form_options['instance'] = rel
        if self.Form:
            self.form = self.Form(self.request.POST, **self.form_options)
            if self.form.is_valid():
                model = self.form.save(commit=True)
                messages.success(self.request, _("Changes saved."))
                #return HttpResponseRedirect('/cmdb/edit/'+str(model.id))
            else:
                messages.error(self.request, _("Correct the errors."))
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
            'form' : self.form,
            'url_query': self.request.GET,
            'relations_parent' : self.relations_parent,
            'relations_child' : self.relations_child,
        })
        return ret

    def form_initial(self):
        data = {
                'parent' : self.rel_parent,
                'child' : self.rel_child,
        }
        return data

    def get(self, *args, **kwargs):
        if not  self.get_permissions().get('edit_configuration_item_relations_perm',False):
            return HttpResponseForbidden()
        self.rel_parent = self.request.GET.get('rel_parent')
        self.rel_child = self.request.GET.get('rel_child')
        ci_id = kwargs.get('ci_id')
        self.ci = get_object_or_404(db.CI, id=ci_id)
        self.relations_parent = [
                x.child for x in  db.CIRelation.objects.filter( parent=ci_id,) ]
        self.relations_child = [
                x.parent for x in db.CIRelation.objects.filter( child=ci_id,) ]
        self.form_options['initial'] = self.form_initial()
        self.form = self.Form(**self.form_options)
        return super(AddRelation, self).get(*args, **kwargs)


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
                model = self.form.save(commit=True)
                messages.success(self.request, _("Changes saved."))
            else:
                messages.error(self.request, _("Correct the errors."))
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
            'form' : self.form,
            'url_query': self.request.GET,
            'label' : 'Add CI',
        })
        return ret

    def get(self, *args, **kwargs):
        self.form = self.Form(**self.form_options)
        return super(Add, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.form = None
        self.ci = None
        if self.Form:
            self.form = self.Form(self.request.POST, **self.form_options)
            if self.form.is_valid():
                model = self.form.save(commit=True)
                if not model.content_object:
                    model.uid = "%s-%s" % ('mm', model.id)
                    model.save()
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
            'last_changes' : self.last_changes,
        })
        return ret

    def get_last_changes(self, ci):
        from ralph.cmdb.integration.jira import Jira
        params = dict(jql='DB\\ CI="%s"' % self.ci_uid)
        xxx=Jira().find_issue(params)
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
        self.ci_uid = kwargs.get('ci_id',None)
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
            list.insert(0,ci)
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
                time__range=(datetime.datetime.now(),datetime.datetime.now()-days)
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
            'form' : self.form,
            'form_attributes' : self.form_attributes,
            'url_query': self.request.GET,
            'ci' : self.ci,
            'ci_id' : self.ci.id,
            'uid' : self.ci.uid,
            'label' : 'Edit CI - ' + self.ci.uid,
            'relations_contains' : self.relations_contains,
            'relations_requires' : self.relations_requires,
            'relations_isrequired' : self.relations_isrequired,
            'relations_parts' : self.relations_parts,
            'relations_hasrole' : self.relations_hasrole,
            'relations_isrole' : self.relations_isrole,
            'puppet_reports' : self.puppet_reports,
            'git_changes': self.git_changes,
            'device_attributes_changes' : self.device_attributes_changes,
            'problems' : self.problems,
            'incidents' : self.incidents,
            'zabbix_triggers' : self.zabbix_triggers,
            'service_name' : self.service_name,
            'so_events' : self.so_events,
            'cmdb_messages' : self.get_messages(),
        })
        return ret


    def custom_form_initial(self, ci):
        data = dict()
        objs = db.CIAttributeValue.objects.filter(ci=ci)
        #FIXME: DRY
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
        #data.update(self.custom_form_initial(ci))
        return data

    def check_perm(self):
        if not  self.get_permissions().get('edit_configuration_item_info_generic_perm',False):
            return HttpResponseForbidden()

    def get_zabbix_data(self):
        try:
            fresh_triggers = zabbix.get_all_triggers(host=self.ci.zabbix_id)
            return [(datetime.datetime.utcfromtimestamp(
                float(x.get('lastchange'))),x) for x in fresh_triggers ]
        except Exception,e:
            return []


    def calculate_relations(self, ci_id):
        self.relations_contains = [ (x,x.child, get_icon_for(x.child)) \
                    for x in db.CIRelation.objects.filter(
                    parent=ci_id, type=db.CI_RELATION_TYPES.CONTAINS.id)
        ]
        self.relations_parts= [ (x,x.parent, get_icon_for(x.parent)) \
                for x in db.CIRelation.objects.filter( child=ci_id,
                type=db.CI_RELATION_TYPES.CONTAINS.id)]
        self.relations_requires = [ (x,x.child, get_icon_for(x.parent)) \
                for x in db.CIRelation.objects.filter( parent=ci_id,
                type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_isrequired = [ (x,x.parent, get_icon_for(x.parent)) \
                for x in db.CIRelation.objects.filter( child=ci_id,
                type=db.CI_RELATION_TYPES.REQUIRES.id)
        ]
        self.relations_hasrole= [ (x,x.child, get_icon_for(x.parent)) \
                for x in db.CIRelation.objects.filter( parent=ci_id,
                type=db.CI_RELATION_TYPES.HASROLE.id)]
        self.relations_isrole= [ (x,x.parent, get_icon_for(x.parent)) \
                for x in db.CIRelation.objects.filter( child=ci_id,
                type=db.CI_RELATION_TYPES.HASROLE.id)]

    def get_ci_id(self):
        """ 2 types of id can land here. """
        ci_id = self.kwargs.get('ci_id')
        if ci_id.find('-')>=0:
            ci = db.CI.objects.get(uid=ci_id)
            return ci.id
        else:
            return self.kwargs.get('ci_id',None)

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
            self.service_name = self.get_first_parent_venture_name(ci_id)
            self.ci = get_object_or_404(db.CI, id=ci_id)
            self.problems = db.CIProblem.objects.filter(
                    ci=self.ci).order_by('-time').all()
            self.incidents = db.CIIncident.objects.filter(
                    ci=self.ci).order_by('-time').all()
            self.git_changes  = [ x.content_object \
                    for x in db.CIChange.objects.filter(
                        ci=self.ci,type=db.CI_CHANGE_TYPES.CONF_GIT.id)]
            self.device_attributes_changes  = [ x.content_object \
                    for x in db.CIChange.objects.filter(
                        ci=self.ci, type=db.CI_CHANGE_TYPES.DEVICE.id) ]

            if self.ci.zabbix_id:
                self.zabbix_triggers = self.get_zabbix_data()
            reps = db.CIChangePuppet.objects.filter(ci=self.ci).all()
            for report in reps:
                puppet_logs = db.PuppetLog.objects.filter(cichange=report).all()
                self.puppet_reports.append(dict(report=report,logs=puppet_logs))
            #self.last_changes = self.get_last_changes(self.ci)
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
        self.relations_parts= []
        self.relations_hasrole= []
        self.relations_isrole= []
        self.relations_isrequired = []
        self.puppet_reports  = []
        self.git_changes = []
        self.device_attributes_changes = []
        self.zabbix_triggers = []
        self.so_events = []
        self.problems = []
        self.incidents = []



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
                    uid = self.ci.uid
                    model = self.form.save(commit=True)
                    model.uid = uid
                    model.save()
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
            'label' : 'View CI:  ' + self.ci.name
        })
        return ret

    def check_perm(self):
        if not  self.get_permissions().get(
                'read_configuration_item_info_generic_perm',False):
            return HttpResponseForbidden()

    def post(self, *args, **kwargs):
        """ Overwrite parent class post """
        return HttpResponseForbidden()

class ViewIframe(View):
    template_name = 'cmdb/view_ci_iframe.html'


class ViewJira(View):
    template_name = 'cmdb/view_ci_iframe.html'

    def get_ci_id(self):
        ci_uid = self.kwargs.get('ci_uid',None)
        ci = db.CI.objects.get(uid=ci_uid)
        #raise 404 in case of missing CI
        return ci.id

    def get_context_data(self, **kwargs):
        ret = super(View, self).get_context_data(**kwargs)
        ret.update({'span_number' : '4' }) #high of screen
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
            'pages' : _get_pages(self.paginator, self.page_number),
            'sort': self.request.GET.get('sort',''),
            'form' : self.form,
            'url_query': self.request.GET,
        })
        return ret

    def form_initial(self, values):
        return values;

    def get(self, *args, **kwargs):
        values = self.request.GET
        cis = db.CI.objects.all()
        if values:
            if values.get('uid'):
                cis = cis.filter(name__icontains=values.get('uid'))
            if values.get('state'):
                cis = cis.filter(state=values.get('state'))
            if values.get('status'):
                cis = cis.filter(status=values.get('status'))
            if values.get('type'):
                cis = cis.filter(type=values.get('type'))
            if values.get('layer'):
                cis = cis.filter(layers=values.get('layer'))
            if values.get('parent'):
                cis = cis.filter(child__parent=int(values.get('parent')))
        sort = self.request.GET.get('sort','name')
        if sort:
            cis = cis.order_by(sort)
        #only top level CI's, not optimized
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
                'count' : i.relations.count(),
                'uid' : i.uid,
                'name' : i.name,
                'ci_type' : i.type.name,
                'id' : i.id,
                'icon' : icon,
                'venture' : '',
                'layers' : ','.join([x[1] for x in i.layers.values_list()]),
                'state' : i.get_state_display(),
                'state_id' : i.state,
                'status' : i.get_status_display(),
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
        ret.update({'error_message' :
            'This Configuration Item cannot be found in the CMDB.' })
        return ret


class RalphView(Info):
    template_name = 'ui/device_info_iframe.html'
    def __init__(self, *args, **kwargs):
        super(Info, self).__init__(*args, **kwargs)

    def get_object(self):
        self.ci_id = self.kwargs.get('ci_id')
        content_object = db.CI.objects.get(id=self.ci_id).content_object
        return content_object



