# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.lib.permissions import ReadOnlyField


class PermByFieldFormMixin(object):
    def __init__(self, *args, **kwargs):
        # TODO: hide fields without view_ perm
        self.read_only_fields = [
            'contract_id',
            'support_type',
            # 'date_to',
            # 'date_from',
        ]
        for field in self.read_only_fields:
            old_field = self.base_fields.get(field)
            if not old_field:
                continue
            self.base_fields[field] = ReadOnlyField(
                label=old_field.label,
                required=False,
                initial=old_field.initial,
                help_text=old_field.help_text,
            )
        super(PermByFieldFormMixin, self).__init__(*args, **kwargs)

    def clean(self):
        """Remove fields without permission from cleaned_data."""
        cleaned_data = super(PermByFieldFormMixin, self).clean()
        for field in self.read_only_fields:
            if field in cleaned_data:
                del cleaned_data[field]
        return cleaned_data
