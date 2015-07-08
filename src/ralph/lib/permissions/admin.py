# -*- coding: utf-8 -*-

from copy import deepcopy


class PermissionAdminMixin(object):
    # TODO: required permissions for add and change
    def get_fieldsets(self, request, obj=None):
        new_fieldsets = []
        fieldsets = super(PermissionAdminMixin, self).get_fieldsets(
            request, obj
        )

        def condition(field):
            can_view = self.model.has_access_to_field(
                field, request.user, 'view'
            )
            can_change = self.model.has_access_to_field(
                field, request.user, 'change'
            )
            return can_view or can_change
        for fieldset in deepcopy(fieldsets):
            fields = [
                field for field in fieldset[1]['fields']
                if condition(field)
            ]
            if not fields:
                continue
            fieldset[1]['fields'] = fields
            new_fieldsets.append(fieldset)
        return new_fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Return read only fields respects user permissions."""
        can_view = self.model.allowed_fields(request.user, 'view')
        can_change = self.model.allowed_fields(request.user, 'change')
        return can_view - can_change

    def get_form(self, request, obj=None, **kwargs):
        """Return form with fields which user have access."""
        kwargs['fields'] = self.model.allowed_fields(request.user)
        return super(PermissionAdminMixin, self).get_form(
            request, obj, **kwargs
        )
