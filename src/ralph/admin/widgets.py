# -*- coding: utf-8 -*-
import os
from itertools import groupby, chain
from urllib import parse

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.views.main import TO_FIELD_VAR
from django.core.exceptions import FieldDoesNotExist
from django.core.urlresolvers import reverse
from django.forms.utils import flatatt
from django.template import loader
from django.template.context import RenderContext
from django.template.defaultfilters import title, slugify
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ralph.admin.autocomplete import QUERY_PARAM, DETAIL_PARAM


ReadOnlyWidget = forms.TextInput(attrs={'readonly': 'readonly'})


class AdminDateWidget(forms.DateInput):
    @property
    def media(self):
        js = map(lambda x: os.path.join(*x), [
            ('vendor', 'js', 'foundation-datepicker.js'),
            ('src', 'js', 'foundation-datepicker-init.js'),
        ])
        return forms.Media(js=[
            static(path) for path in js
        ])

    def render(self, name, value, attrs=None):
        attrs['class'] = 'datepicker'
        return super(AdminDateWidget, self).render(name, value, attrs=attrs)


class PermissionsSelectWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs)
        self.choices = list(choices)

    @property
    def media(self):
        js = ['multi.js']
        return forms.Media(js=[
            static(os.path.join('src', 'js', path)) for path in js
        ])

    def value_from_datadict(self, data, files, name):
        values = data.get(name)
        if not values:
            return
        return list(map(int, values.split(',')))

    def render(self, name, value, attrs=None, choices=()):
        attr_value = ','.join(map(str, value or []))
        final_attrs = self.build_attrs(
            attrs, type='hidden', name=name, value=attr_value,
        )
        return mark_safe(
            '<a class="expand action-expand">Expand all</a>'
            '<ul class="accordion" data-multi="{}" data-accordion>{}</ul>'
            '<input{} />'.format(
                name, self.render_options(choices, value), flatatt(final_attrs)
            )
        )

    def render_all_option(self, slug):
        return (
            '<input class="select-all" id="id_all_{id_name}" type="checkbox">'
            '<label for="id_all_{id_name}">{label}</label><br>'
        ).format(id_name=slug, label=_('All'))

    def render_option(self, selected_choices, option_value, option_label):
        input_id = 'id_option_{}'.format(option_value)
        attrs = {'id': input_id, 'type': 'checkbox', 'value': option_value}
        if option_value in selected_choices:
            attrs['checked'] = 'checked'
        attrs = self.build_attrs(**attrs)
        return '<input{}><label{}>{}</label>'.format(
            flatatt(attrs), flatatt({'for': input_id}), option_label
        )

    def render_options(self, choices, selected_choices):
        separator = ' | '
        choices = sorted(
            chain(self.choices, choices),
            key=lambda x: x[1].split(separator)[1]
        )
        grouped = groupby(choices, lambda x: x[1].split(separator)[1])
        rendered_options = ''
        for group_key, group_choices in grouped:
            items = list(group_choices)
            local_values = [item[0] for item in items]
            local_selected = set(local_values) & set(selected_choices or [])
            slug = slugify(group_key)
            label = title(group_key)
            rendered_options += mark_safe(
                '<li class="accordion-navigation">'
                    '<a href="#{slug}">'
                        '{title}<i class="right">'
                            '<span class="counter">{selected}</span> of {total}'
                        '</i>'
                    '</a>'
                    '<div id="{slug}" class="content">'
                        '{all}{items}'
                    '</div>'  # noqa
                '</li>'.format(
                    slug=slug,
                    title=label,
                    selected=len(local_selected),
                    total=len(local_values),
                    all=self.render_all_option(slugify(group_key)),
                    items='<br />'.join([
                        self.render_option(
                            local_selected, c[0], c[1].split(separator)[-1]
                        ) for c in items
                    ])
                )
            )
        return rendered_options


class AutocompleteWidget(forms.TextInput):
    def __init__(self, rel, admin_site, attrs=None, using=None):
        self.rel = rel
        self.admin_site = admin_site
        self.db = using
        super().__init__(attrs)

    @property
    def media(self):
        return forms.Media(js=[
            os.path.join('src', 'js', 'ralph-autocomplete.js')
        ])

    def get_url_parameters(self):
        params = {
            TO_FIELD_VAR: self.rel.get_related_field().name,
        }
        return '?' + parse.urlencode(params)

    def render(self, name, value, attrs=None):
        rel_to = self.rel.to
        admin_model = self.admin_site._registry[rel_to]
        model_options = rel_to._meta.app_label, rel_to._meta.model_name
        widget_options = {
            'data-suggest-url': reverse(
                'admin:{}_{}_autocomplete_suggest'.format(*model_options)
            ),
            'data-details-url': reverse(
                'admin:{}_{}_autocomplete_details'.format(*model_options)
            ),
            'data-query-var': QUERY_PARAM,
            'data-detail-var': DETAIL_PARAM,
        }

        if attrs is None:
            attrs = {}
        attrs.update({'type': 'hidden'})
        widget_options['data-target-selector'] = '#' + attrs.get('id')
        input_field = super().render(name, value, attrs)

        if rel_to in self.admin_site._registry:
            related_url = reverse(
                'admin:%s_%s_changelist' % (
                    rel_to._meta.app_label,
                    rel_to._meta.model_name,
                ),
                current_app=self.admin_site.name,
            ) + self.get_url_parameters()
            searched_fields = []
            for field_name in admin_model.search_fields:
                try:
                    searched_fields.append(
                        str(rel_to._meta.get_field(field_name).verbose_name)
                    )
                except FieldDoesNotExist:
                    pass

        context = RenderContext({
            'current_object': rel_to.objects.filter(
                pk=value or None
            ).first() or None,
            'attrs': flatatt(widget_options),
            'related_url': related_url,
            'name': name,
            'input_field': input_field,
            'searched_fields': ', '.join(searched_fields),
        })
        template = loader.get_template('admin/widgets/autocomplete.html')
        return template.render(context)
