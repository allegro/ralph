# -*- coding: utf-8 -*-
from django import forms
from django.conf.urls import url
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from ralph.admin.fields import MultilineField, MultivalueFormMixin
from ralph.admin.mixins import RalphTemplateView
from ralph.admin.sites import ralph_site


class MultiAddView(RalphTemplateView):

    """Adding view to multiple adds models."""

    template_name = 'admin/multi_add.html'

    def dispatch(self, request, object_pk, model, *args, **kwargs):
        admin_model = ralph_site._registry[model]
        self.model = model
        self.fields = admin_model.get_multiadd_fields()
        self.info_fields = admin_model.multiadd_info_fields
        self.obj = get_object_or_404(model, pk=object_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        form_kwargs = {}
        multi_form_attrs = {
            'multivalue_fields': self.fields,
            'model': self.model
        }
        for field in self.fields:
            multi_form_attrs[field] = MultilineField(allow_duplicates=False)

        multi_form = type(
            'MultiForm', (MultivalueFormMixin, forms.Form), multi_form_attrs
        )
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        return multi_form(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['obj'] = self.obj
        context['info_fields'] = self.info_fields
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
        context['form'] = form
        return self.render_to_response(context)

    def get_url_name(self):
        """
        Return URl for model change list.
        """
        params = self.model._meta.app_label, self.model._meta.model_name
        url = 'admin:{}_{}_changelist'.format(*params)
        return reverse(url)

    def _get_ancestors_pointers(self, model):
        result = []
        for parent_model, parent_field in model._meta.parents.items():
            result.append(parent_field.column)
            result.extend(self._get_ancestors_pointers(parent_model))
        return result

    @transaction.atomic
    def form_valid(self, form):
        saved_assets = []
        args = [form.cleaned_data[field] for field in self.fields]
        for data in zip(*args):
            for field in self._get_ancestors_pointers(self.obj):
                setattr(self.obj, field, None)
            self.obj.id = self.obj.pk = None

            for i, field in enumerate(self.fields):
                setattr(self.obj, field, data[i])

            self.obj.save()
            saved_assets.append(str(self.obj))

        messages.success(
            self.request, _('Saved %(assets)s assets') % {
                'assets': ", ".join(saved_assets)
            }
        )
        return HttpResponseRedirect(self.get_url_name())


class MulitiAddAdminMixin(object):

    """
    Multi add admin mixin.

    Add the ability to multiple add records to Django admin view.

    Example:
    >>> class MyAdminView(admin.ModelAdmin, MulitiAddAdminMixin):
    ...     def get_multiadd_fields(self):
    ...         return ['field1', 'field2']
    ...     multiadd_info_fields = ['field1', 'field2']
    ...     # Fields that displays information about the copied object

    """

    view = MultiAddView

    def get_url_name(self, with_namespace=True):
        params = self.model._meta.app_label, self.model._meta.model_name
        url = '{}_{}_multiadd'.format(*params)
        if with_namespace:
            url = 'admin:' + url
        return url

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context.update({
            'multi_add_url': reverse(self.get_url_name(), args=[object_id])
        })

        return super().change_view(
            request, object_id, form_url, extra_context
        )

    def get_urls(self):
        urls = super().get_urls()
        _urls = [
            url(
                r'^(?P<object_pk>.+)/multiadd/$',
                self.admin_site.admin_view(self.view.as_view()),
                {'model': self.model},
                name=self.get_url_name(False),
            ),
        ]
        return _urls + urls
