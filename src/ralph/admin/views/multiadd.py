# -*- coding: utf-8 -*-
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django import forms
from django.forms.models import modelformset_factory
from ralph.back_office.models import BackOfficeAsset, Warehouse
from django.forms.formsets import formset_factory
from ralph.admin.mixins import RalphTemplateView
from django.db import transaction
from django.conf.urls import url
from ralph.admin.fields import MultilineField, MultivalueFormMixin
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from django.db import IntegrityError
from django.shortcuts import render_to_response

class MultiAddView(RalphTemplateView):
    template_name = 'admin/xxx.html'

    def dispatch(
        self, request, object_pk, model, *args, **kwargs
    ):
        self.obj = get_object_or_404(model, pk=object_pk)
        #self.transition = get_object_or_404(Transition, pk=transition_pk)
        #self.actions = self.collect_actions(self.transition)
        return super().dispatch(request, *args, **kwargs)

    #def collect_actions(self, transition):
    #    names = transition.actions.values_list('name', flat=True).all()
    #    return [getattr(self.obj, name) for name in names]

    #def get_form_fields_from_actions(self):
    #    fields = {}
    #    for action in self.actions:
    #        action_fields = getattr(action, 'form_fields', {})
    #        for name, field in action_fields.items():
    #            field.widget.request = self.request
    #            fields['{}__{}'.format(action.__name__, name)] = field
    #    return fields

    def get_form(self):
        form_kwargs = {}
        class BackOfficeAssetMultiForm(MultivalueFormMixin, forms.Form):
            multivalue_fields = ['sn', 'barcode']
            sn = MultilineField(allow_duplicates=False)
            barcode = MultilineField(allow_duplicates=False)
            model = BackOfficeAsset
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        return BackOfficeAssetMultiForm(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['asset'] = self.obj
        context['back_url'] = self.obj.get_absolute_url()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                return self.form_valid(form)
            except IntegrityError as e:
                context = self.get_context_data()
                context['form'] = form
                form.add_error(None, e.args[1])
                return self.render_to_response(context)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        return self.render_to_response(context)

    @transaction.atomic
    def form_valid(self, form):
        for barcode, sn in zip(
            form.cleaned_data['barcode'], form.cleaned_data['sn']
        ):
            self.obj.baseobject_ptr_id = None
            self.obj.asset_ptr_id = None
            self.obj.id = self.obj.pk = None
            self.obj.barcode = barcode
            self.obj.sn = sn
            self.obj.save()
        messages.success(
            self.request, _('saved many assets successfully with no fuss')
        )
        return HttpResponseRedirect(self.obj.get_absolute_url())


class MulitiAddAdminMixin(object):
    run_transition_view = MultiAddView

    def get_transition_url_name(self, with_namespace=True):
        params = self.model._meta.app_label, self.model._meta.model_name
        url = '{}_{}_transition'.format(*params)
        if with_namespace:
            url = 'admin:' + url
        return url

    def change_view(self, request, object_id, form_url='', extra_context=None):
        #TODO:: rm it
        if not extra_context:
            extra_context = {}
        extra_context.update({
            'transition_url_name': self.get_transition_url_name()
        })
        return super().changeform_view(
            request, object_id, form_url, extra_context
        )

    def get_urls(self):
        urls = super().get_urls()
        _urls = [
            url(
                #r'^(?P<object_pk>.+)/transition/(?P<transition_pk>\d+)$',
                r'^(?P<object_pk>.+)/multiadd/$',
                self.admin_site.admin_view(self.run_transition_view.as_view()),
                {'model': self.model},
                name='myxxx',
                #name=self.get_transition_url_name(False),
            ),
        ]
        return _urls + urls
