# -*- coding: utf-8 -*-
from django import forms
from django.conf.urls import url
from django.contrib import messages
from django.db import IntegrityError, models, transaction
from django.forms import ValidationError
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ralph.admin.fields import (
    IntegerMultilineField,
    MultilineField,
    MultivalueFormMixin
)
from ralph.admin.mixins import RalphTemplateView
from ralph.admin.sites import ralph_site
from ralph.helpers import get_model_view_url_name


class MultiAddView(RalphTemplateView):
    """Adding view to multiple adds models."""

    template_name = "admin/multi_add.html"

    def dispatch(self, request, object_pk, model, *args, **kwargs):
        admin_model = ralph_site._registry[model]
        self.model = model
        if not request.user.has_perm(
            "{}.add_{}".format(self.model._meta.app_label, self.model._meta.model_name)
        ):
            return HttpResponseForbidden()
        self.info_fields = admin_model.multiadd_info_fields
        self.obj = get_object_or_404(model, pk=object_pk)
        self.fields = admin_model.get_multiadd_fields(obj=self.obj)
        self.clear_fields = admin_model.get_multiadd_clear_fields(obj=self.obj)
        self.one_of_mulitval_required = admin_model.one_of_mulitvalue_required
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        form_kwargs = {}
        multi_form_attrs = {
            "multivalue_fields": [i["field"] for i in self.fields],
            "model": self.model,
            "one_of_mulitvalue_required": self.one_of_mulitval_required,
        }
        for item in self.fields:
            field_type = self.model._meta.get_field(item["field"])
            required = item.get("required", not field_type.blank)
            if isinstance(field_type, models.IntegerField):
                multi_form_attrs[item["field"]] = IntegerMultilineField(
                    allow_duplicates=item["allow_duplicates"],
                    required=required,
                )
            else:
                multi_form_attrs[item["field"]] = MultilineField(
                    allow_duplicates=item["allow_duplicates"],
                    required=required,
                )

        multi_form = type(
            "MultiForm", (MultivalueFormMixin, forms.Form), multi_form_attrs
        )
        if self.request.method == "POST":
            form_kwargs["data"] = self.request.POST
        return multi_form(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["obj"] = self.obj
        context["info_fields"] = self.info_fields
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                return self.form_valid(form)
            except IntegrityError as e:
                context = self.get_context_data()
                context["form"] = form
                form.add_error(None, e.args[1])
                return self.render_to_response(context)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)

    def get_url_name(self):
        """
        Return URl for model change list.
        """
        params = self.model._meta.app_label, self.model._meta.model_name
        url = "admin:{}_{}_changelist".format(*params)
        return reverse(url)

    def _get_ancestors_pointers(self, model):
        result = []
        for parent_model, parent_field in model._meta.parents.items():
            result.append(parent_field.column)
            result.extend(self._get_ancestors_pointers(parent_model))
        return result

    @transaction.atomic
    def form_valid(self, form):
        saved_objects = []
        args = [form.cleaned_data[field["field"]] for field in self.fields]
        for data in zip(*args):
            for field in self._get_ancestors_pointers(self.obj):
                setattr(self.obj, field, None)
            self.obj.id = self.obj.pk = None

            for field in self.clear_fields:
                setattr(self.obj, field["field"], field["value"])

            for i, field in enumerate(self.fields):
                setattr(self.obj, field["field"], data[i])

            try:
                self.obj.clean()
            except ValidationError as exc:
                for error in exc:
                    form.add_error(error[0], error[1])
                return self.form_invalid(form)

            self.obj.save()
            saved_objects.append(
                '<a href="{}">{}</a>'.format(self.obj.get_absolute_url(), str(self.obj))
            )

        messages.success(
            self.request,
            mark_safe(
                _("Saved %(count)d object(s): %(objects)s")
                % {"count": len(saved_objects), "objects": ", ".join(saved_objects)}
            ),
        )
        return HttpResponseRedirect(self.get_url_name())


class MulitiAddAdminMixin(object):
    """
    Multi add admin mixin.

    Add the ability to multiple add records to Django admin view.

    Example:
    >>> class MyAdminView(admin.ModelAdmin, MulitiAddAdminMixin):
    ...     def get_multiadd_fields(self, obj=None):
    ...         return [{'field': 'field1', 'allow_duplicates': False}]
    ...     multiadd_info_fields = ['field1', 'field2']
    ...     # Fields that displays information about the copied object

    """

    view = MultiAddView
    one_of_mulitvalue_required = []
    multiadd_clear_fields = []

    @property
    def multiadd_info_fields(self):
        return self.list_display

    def get_multiadd_fields(self, obj=None):
        raise NotImplementedError()

    def get_multiadd_clear_fields(self, obj=None):
        return self.multiadd_clear_fields

    def get_url_name(self, with_namespace=True):
        return get_model_view_url_name(self.model, "multiadd", with_namespace)

    def add_view(self, request, form_url="", extra_context=None):
        if not extra_context:
            extra_context = {}
        if self.has_add_permission(request):
            extra_context.update({"multi_add_field": True})
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if not extra_context:
            extra_context = {}
        if self.has_add_permission(request):
            extra_context.update(
                {"multi_add_url": reverse(self.get_url_name(), args=[object_id])}
            )

        return super().change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        _urls = [
            url(
                r"^(?P<object_pk>.+)/multiadd/$",
                self.admin_site.admin_view(self.view.as_view()),
                {"model": self.model},
                name=self.get_url_name(False),
            ),
        ]
        return _urls + urls

    def response_add(self, request, obj, post_url_continue=None):
        """
        Override response add from django model admin.

        Adding support for multiadd.
        """
        if "_multi_add" in request.POST:
            return HttpResponseRedirect(reverse(self.get_url_name(), args=[obj.pk]))
        return super().response_add(request, obj, post_url_continue)
