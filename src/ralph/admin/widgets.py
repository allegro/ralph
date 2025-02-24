# -*- coding: utf-8 -*-
import copy
import json
import logging
import os
from collections import defaultdict
from itertools import chain, groupby
from urllib import parse

from django import forms
from django.apps import apps
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.views.main import TO_FIELD_VAR
from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import flatatt
from django.template import loader
from django.template.context import RenderContext
from django.template.defaultfilters import slugify, title
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ralph.admin.autocomplete import get_results
from ralph.admin.helpers import get_field_by_relation_path

ReadOnlyWidget = forms.TextInput(attrs={"readonly": "readonly"})

logger = logging.getLogger(__name__)


class DatepickerWidgetMixin:
    css_class = "datepicker"

    @property
    def media(self):
        js = map(
            lambda x: os.path.join(*x),
            [
                ("vendor", "js", "foundation-datepicker.js"),
                ("src", "js", "foundation-datepicker-init.js"),
            ],
        )
        return forms.Media(js=[static(path) for path in js])

    def render(self, name, value, attrs=None, renderer=None):
        attrs["class"] = self.css_class
        return super().render(name, value, attrs=attrs, renderer=renderer)


class AdminDateWidget(DatepickerWidgetMixin, forms.DateInput):
    css_class = "datepicker"


class AdminDateTimeWidget(DatepickerWidgetMixin, forms.DateTimeInput):
    css_class = "datepicker-with-time"


class PermissionsSelectWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs)
        self.choices = list(choices)

    @property
    def media(self):
        js = ["multi.js"]
        return forms.Media(js=[static(os.path.join("src", "js", path)) for path in js])

    def value_from_datadict(self, data, files, name):
        values = data.get(name)
        if not values:
            return
        return list(map(int, values.split(",")))

    def render(self, name, value, attrs=None, choices=()):
        attr_value = ",".join(map(str, value or []))
        if not attrs:
            attrs = {}
        final_attrs = self.build_attrs(
            attrs, extra_attrs={"type": "hidden", "name": name, "value": attr_value}
        )
        return mark_safe(
            '<a class="expand action-expand">Expand all</a>'
            '<ul class="accordion" data-multi="{}" data-accordion>{}</ul>'
            "<input{} />".format(
                name, self.render_options(choices, value), flatatt(final_attrs)
            )
        )

    def render_all_option(self, slug):
        return (
            '<input class="select-all" id="id_all_{id_name}" type="checkbox">'
            '<label for="id_all_{id_name}">{label}</label><br>'
        ).format(id_name=slug, label=_("All"))

    def render_option(self, selected_choices, option_value, option_label):
        input_id = "id_option_{}".format(option_value)
        attrs = {"id": input_id, "type": "checkbox", "value": option_value}
        if option_value in selected_choices:
            attrs["checked"] = "checked"
        attrs = self.build_attrs({**attrs})
        return "<input{}><label{}>{}</label>".format(
            flatatt(attrs), flatatt({"for": input_id}), option_label
        )

    def render_options(self, choices, selected_choices):
        separator = " | "
        choices = sorted(
            chain(self.choices, choices), key=lambda x: x[1].split(separator)[1].lower()
        )
        grouped = groupby(choices, lambda x: x[1].split(separator)[1])
        rendered_options = ""
        for group_key, group_choices in grouped:
            items = list(group_choices)
            local_values = [item[0] for item in items]
            local_selected = set(local_values) & set(selected_choices or [])
            slug = slugify(group_key)
            label = title(group_key)
            rendered_options += mark_safe(
                """
                <li class="accordion-navigation">
                    <a href="#{slug}">
                        {title}<i class="right">
                            <span class="counter">{selected}</span> of {total}
                        </i>
                    </a>
                    <div id="{slug}" class="content">
                        {all}{items}
                    </div>
                </li>""".format(
                    slug=slug,
                    title=label,
                    selected=len(local_selected),
                    total=len(local_values),
                    all=self.render_all_option(slugify(group_key)),
                    items="<br />".join(
                        [
                            self.render_option(
                                local_selected, c[0], c[1].split(separator)[-1]
                            )
                            for c in items
                        ]
                    ),
                )
            )
        return rendered_options


class AutocompleteWidget(forms.TextInput):
    multivalue_separator = ","

    def __init__(self, field, admin_site, attrs=None, using=None, **kwargs):
        self.field = field
        self.rel = self.field.remote_field
        self.multi = kwargs.get("multi", False)
        self.request = kwargs.get("request", None)
        self.rel_to = kwargs.get("rel_to") or field.remote_field.model
        self.admin_site = admin_site
        self.db = using
        super().__init__(attrs)

    @property
    def can_edit(self):
        return self.admin_site._registry[self.rel_to].has_change_permission(
            self.request
        )

    @property
    def can_add(self):
        return self.admin_site._registry[self.rel_to].has_add_permission(self.request)

    @property
    def media(self):
        res = forms.Media(
            js=[
                os.path.join("src", "js", "ralph-autocomplete.js"),
                "admin/js/core.js",
            ]
        )
        return res

    def get_url_parameters(self):
        params = {
            TO_FIELD_VAR: self.rel.get_related_field().name,
        }
        return "?" + parse.urlencode(params)

    def get_related_url(self, info, action, *args):
        return reverse(
            "admin:%s_%s_%s" % (info + (action,)),
            current_app=self.admin_site.name,
            args=args,
        )

    def get_prefetch_data(self, value):
        results = {}
        if value:
            queryset = self.rel_to._default_manager.filter(
                pk__in=value if self.multi else [value]
            )
            results = get_results(queryset, self.can_edit)
        return json.dumps(results)

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if self.multi:
            if value:
                value = value.split(self.multivalue_separator)
            else:
                value = []
        return value

    def _get_model_search_fields(self, model):
        """Gets `model`'s search fields."""
        search_fields_tooltip = defaultdict(list)
        for field_name in self.admin_site._registry[model].search_fields:
            try:
                field = get_field_by_relation_path(model, field_name)
                key = str(model._meta.verbose_name)
                search_fields_tooltip[key].append(str(field.verbose_name))
            except FieldDoesNotExist as e:
                logger.error(e)
        return search_fields_tooltip

    def get_search_fields(self):
        polymorphic_descendants = getattr(self.rel_to, "_polymorphic_descendants", [])

        if polymorphic_descendants:
            # Check if model after which we are looking for is polymorphic
            # if they are also looking for the models of its dependencies
            # or by limit_models defined in model
            polymorphic_models = polymorphic_descendants
            limit_models = getattr(self.field, "limit_models", [])
            if limit_models:
                polymorphic_models = [
                    apps.get_model(*i.split(".")) for i in limit_models
                ]

            search_fields_tooltip = defaultdict(list)
            for related_model in polymorphic_models:
                found = self._get_model_search_fields(related_model)
                search_fields_tooltip.update(found)

        else:
            search_fields_tooltip = self._get_model_search_fields(self.rel_to)
        return search_fields_tooltip

    def render_search_fields_info(self, search_fields):
        rows = ["Search by:\n"]
        for model, fields in search_fields.items():
            rows.append("{}:\n".format(model.capitalize()))
            for field in fields:
                rows.append("- {}\n".format(field))
        return "".join(rows)

    def render(self, name, value, attrs=None, renderer=None):
        model_options = (self.rel_to._meta.app_label, self.rel_to._meta.model_name)
        original_value = copy.copy(value)
        if attrs is None:
            attrs = {}
        attrs["name"] = name
        if self.multi:
            value = value or []
            attrs["multi"] = "true"
            value = self.multivalue_separator.join(force_text(v) for v in value)
        else:
            value = value or ""

        search_fields = self.get_search_fields()
        search_fields_info = self.render_search_fields_info(dict(search_fields))

        if self.rel_to in self.admin_site._registry:
            related_url = (
                reverse(
                    "admin:%s_%s_changelist"
                    % (
                        self.rel_to._meta.app_label,
                        self.rel_to._meta.model_name,
                    ),
                    current_app=self.admin_site.name,
                )
                + self.get_url_parameters()
            )

        context = RenderContext(
            {
                "model": str(self.rel_to._meta.verbose_name),
                "data_suggest_url": reverse(
                    "autocomplete-list",
                    kwargs={
                        "app": self.field.remote_field.related_model._meta.app_label,
                        "model": self.field.remote_field.related_model._meta.model_name,
                        "field": self.field.name,
                    },
                ),
                "data_details_url": reverse(
                    "admin:{}_{}_autocomplete_details".format(*model_options)
                ),
                "name": name or "",
                "value": value,
                "attrs": flatatt(attrs),
                "related_url": related_url,
                "search_fields_info": search_fields_info,
                "prefetch_data": self.get_prefetch_data(original_value),
            }
        )

        info = (self.rel_to._meta.app_label, self.rel_to._meta.model_name)
        is_polymorphic = getattr(self.rel_to, "is_polymorphic", False)
        if not is_polymorphic and self.can_add:
            context["add_related_url"] = self.get_related_url(info, "add")
        template = loader.get_template("admin/widgets/autocomplete.html")
        return template.render(context.flatten())
