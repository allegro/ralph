# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType

from ralph.admin.decorators import register
from ralph.admin.mixins import RalphAdmin, RalphGenericTabularInline
from ralph.lib.custom_fields.forms import (
    CustomFieldValueForm,
    CustomFieldValueFormSet,
    CustomFieldValueWithClearChildrenForm
)
from ralph.lib.custom_fields.models import CustomField, CustomFieldValue
from ralph.lib.custom_fields.views import CustomFieldFormfieldView


@register(CustomField)
class CustomFieldAdmin(RalphAdmin):
    list_display = [
        'name', 'attribute_name', 'type', 'default_value',
        'use_as_configuration_variable'
    ]
    search_fields = ['name', 'attribute_name']
    list_filter = ['type']
    fields = [
        'name', 'attribute_name', 'type', 'choices', 'default_value',
        'managing_group', 'use_as_configuration_variable'
    ]
    readonly_fields = ['attribute_name']

    def get_urls(self):
        """
        Expose extra "<custom_field>/formfield" url for returning custom field
        formfield html.
        """
        urls = super().get_urls()
        my_urls = [
            url(
                r'^(?P<custom_field_id>.+)/formfield/$',
                CustomFieldFormfieldView.as_view(),
                name='customfield_formfield'
            ),
        ]
        return my_urls + urls


class CustomFieldValueInline(RalphGenericTabularInline):
    model = CustomFieldValue
    form = CustomFieldValueForm
    formset = CustomFieldValueFormSet
    raw_id_fields = ['custom_field']
    template = 'custom_fields/edit_inline/tabular.html'


class CustomFieldValueWithClearChildrenInline(CustomFieldValueInline):
    form = CustomFieldValueWithClearChildrenForm


class CustomFieldValueAdminMixin(object):
    # set to True if custom field values summary should be visible
    # if set to False, inline form with custom fields will be shown with 100%
    # width
    show_custom_fields_values_summary = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inlines = list(self.inlines) + [
            self._get_custom_field_value_inline()
        ]

    def _get_custom_field_value_inline(self):
        # check if any model is inheriting custom fields from current model
        if self.model._meta.custom_fields_inheritance_by_model:
            # if yes, allow for clearing custom fields values of children
            # objects
            return CustomFieldValueWithClearChildrenInline
        return CustomFieldValueInline

    @staticmethod
    def _get_custom_fields_values(obj):
        """
        Return custom fields values (summary, with inherited values) for
        current object, sorted by custom field name.

        Fields for single item:
        * name - name of the custom field
        * value - value of the custom field
        * object - name of the object, from which CFV is inherited, if it's
          inherited, otherwise <none>
        * object_url - absolute url to object from which CFV is inherited, if
          it's inherited, otherwise ''

        :rtype: list of dicts
        """
        result = []
        obj_content_type_id = ContentType.objects.get_for_model(obj).id
        for cfv in obj.custom_fields.select_related('custom_field').order_by(
            'custom_field__name'
        ):
            if (
                cfv.content_type_id == obj_content_type_id and
                cfv.object_id == obj.pk
            ):
                object = '-'
                object_url = ''
            else:
                object = '{}: {}'.format(
                    cfv.content_type.model_class()._meta.verbose_name,
                    cfv.object
                )
                object_url = cfv.object.get_absolute_url()
            cfv_data = {
                'name': cfv.custom_field.name,
                'value': cfv.value,
                'object': object,
                'object_url': object_url,
            }
            result.append(cfv_data)
        return result

    def changeform_view(
        self, request, object_id=None, form_url='', extra_context=None
    ):
        if extra_context is None:
            extra_context = {}
        extra_context['custom_fields_values_summary'] = (
            self.show_custom_fields_values_summary and object_id
        )
        if self.show_custom_fields_values_summary and object_id:
            obj = self.get_object(request, unquote(object_id))
            if obj:
                extra_context['custom_fields_all'] = (
                    self._get_custom_fields_values(obj)
                )
        return super().changeform_view(
            request, object_id, form_url, extra_context
        )

    def _create_formsets(self, request, obj, change):
        """
        Helper function to generate formsets for add/change_view

        99% of this function contains unaltered code from Django. The only
        alternation is that it passes request objects to custom field form sets
        in order to make it impossible to edit restricted custom fields.

        """
        formsets = []
        inline_instances = []
        prefixes = {}
        get_formsets_args = [request]
        if change:
            get_formsets_args.append(obj)
        for FormSet, inline in self.get_formsets_with_inlines(*get_formsets_args):  # noqa: E501
            prefix = FormSet.get_default_prefix()
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1 or not prefix:
                prefix = "%s-%s" % (prefix, prefixes[prefix])
            formset_params = {
                'instance': obj,
                'prefix': prefix,
                'queryset': inline.get_queryset(request),
            }

            if issubclass(FormSet, CustomFieldValueFormSet):
                formset_params['request'] = request

            if request.method == 'POST':
                formset_params.update({
                    'data': request.POST,
                    'files': request.FILES,
                    'save_as_new': '_saveasnew' in request.POST
                })
            formsets.append(FormSet(**formset_params))
            inline_instances.append(inline)
        return formsets, inline_instances
