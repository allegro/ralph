from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from ralph.lib.custom_fields.models import CustomField


class CustomFieldFormfieldView(View):
    """
    Return HTML for custom field formfield.
    """
    http_method_names = ['get']

    def get(self, request, custom_field_id, *args, **kwargs):
        custom_field = get_object_or_404(CustomField, pk=custom_field_id)
        form_field = custom_field.get_form_field()
        return HttpResponse(form_field.widget.render(
            name='__empty__',
            value=form_field.initial
        ))
