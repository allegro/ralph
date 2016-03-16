# -*- coding: utf-8 -*-
from django.forms import ValidationError
from django.forms.models import BaseInlineFormSet


def validate_is_management(forms):
    """
    Validate is_management field in IpAddress formset
    """
    is_management = []
    for form in forms:
        cleaned_data = form.cleaned_data
        if (
            cleaned_data and
            not cleaned_data.get('DELETE', False)
        ):
            is_management.append(cleaned_data.get('is_management'))

    count_management_ip = is_management.count(True)
    if is_management and count_management_ip == 0:
        raise ValidationError(
            'One IP address must be management'
        )
    elif is_management and count_management_ip != 1:
        raise ValidationError((
            'Only one managment IP address can be assigned '
            'to this asset'
        ))


class NetworkInlineFormset(BaseInlineFormSet):

    def clean(self):
        validate_is_management(self.forms)
