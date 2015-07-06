# -*- coding: utf-8 -*-
import os
from itertools import groupby, chain

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.forms.utils import flatatt
from django.template.defaultfilters import title, slugify
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


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
