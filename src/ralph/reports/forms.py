from collections import Counter

from django import forms
from django.contrib.admin.options import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _


class ReportTemplateFormset(BaseInlineFormSet):
    def clean(self):
        defaults = [row["default"] for row in getattr(self, "cleaned_data", [])]
        counted = Counter(defaults)[True]
        if counted != 1:
            raise forms.ValidationError(_("Please select exactly one default item."))
