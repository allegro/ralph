# -*- coding: utf-8 -*-
"""
Apply Ralph permissions (per field and per object) to django-import-export
resources used in admin.
"""

from collections import OrderedDict
from copy import copy

from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist, PermissionDenied
from django.db.models.constants import LOOKUP_SEP
from django.utils.translation import gettext_lazy as _

from ralph.lib.permissions.models import PermByFieldMixin, PermissionsForObjectMixin
from ralph.lib.polymorphic.models import Polymorphic


def _get_concrete_object(obj):
    """
    Return the most specific (descendant) instance of polymorphic object, ex.
    `BackOfficeAsset` for `BaseObject` selected as foreign key target, to
    be able to check its object permissions.
    """
    if isinstance(obj, PermissionsForObjectMixin) or not isinstance(obj, Polymorphic):
        return obj
    if not obj.content_type_id:
        return obj
    try:
        return obj.last_descendant
    except (ObjectDoesNotExist, AttributeError):
        return obj


def _get_model_field(model, name):
    try:
        return model._meta.get_field(name)
    except FieldDoesNotExist:
        pass
    # foreign keys could be referenced by attname (ex. `manufacturer_id`)
    for field in model._meta.concrete_fields:
        if field.attname == name:
            return field
    return None


def _get_fields_to_check(model, attribute):
    """
    Return list of (model, field_name) pairs which permissions have to be
    checked to access `attribute` (which could span relations, ex.
    `support__name`).
    """
    result = []
    for part in attribute.split(LOOKUP_SEP):
        if model is None:
            break
        field = _get_model_field(model, part)
        if field is None:
            # not a model field (property, method etc.) - check permissions
            # to `_permission_field` if defined (the same as in admin)
            perm_field = getattr(getattr(model, part, None), "_permission_field", None)
            if perm_field:
                result.append((model, perm_field))
            break
        # skip reverse relations (there are no permissions for them) and
        # primary keys (which are required to identify rows)
        is_forward = not field.auto_created or field.concrete
        if is_forward and not field.primary_key:
            result.append((model, field.name))
        model = getattr(field, "related_model", None)
    return result


def _get_permission_attribute(resource_class, name, field):
    """
    Return attribute used to check permissions to resource field.

    Fields which do not expose a model field directly (computed fields
    without `attribute` or reverse accessors like `baseobjectssupport_set`)
    have to declare it explicitly in `computed_fields_permissions` of
    resource (mapping from field name or field attribute to the model field
    path used to check permissions). Attribute mapping covers also generated
    `*_str` export variants of the field.
    """
    mapping = getattr(resource_class, "computed_fields_permissions", {})
    for key in (name, field.attribute):
        if key and key in mapping:
            return mapping[key]
    return field.attribute or ""


def has_access_to_attribute(model, attribute, user, action):
    """
    Check if user has `action` (view/change) permission to resource field
    attribute.
    """
    if not attribute:
        return True
    for field_model, field_name in _get_fields_to_check(model, attribute):
        if not issubclass(field_model, PermByFieldMixin):
            continue
        if not field_model.has_access_to_field(field_name, user, action):
            return False
    return True


class RestrictedResourceMixin:
    """
    Mixin for resources created by `restrict_resource_class`. Validates
    permissions during import.
    """

    _ralph_user = None
    _forbidden_import_columns = frozenset()
    _scope_filter = None

    def before_import(self, dataset, **kwargs):
        forbidden = set(dataset.headers or []) & self._forbidden_import_columns
        if forbidden:
            raise PermissionDenied(
                _("You don't have permissions to import columns: %(columns)s")
                % {"columns": ", ".join(sorted(forbidden))}
            )
        return super().before_import(dataset, **kwargs)

    def _check_object_permission(self, instance):
        if isinstance(instance, PermissionsForObjectMixin) and not (
            instance.has_permission_to_object(self._ralph_user)
        ):
            raise PermissionDenied(_("You don't have permissions to this object"))
        self._check_object_scope(instance)

    def _check_object_scope(self, instance):
        """
        Check if object is in scope allowed for the user (ex. visibility
        scope applied in admin's queryset).
        """
        if self._scope_filter is None or instance.pk is None:
            return
        if not (
            type(instance)._default_manager.filter(self._scope_filter, pk=instance.pk).exists()
        ):
            raise PermissionDenied(_("You don't have permissions to this object"))

    def _check_related_objects_permissions(self, instance, row):
        """
        Check if user has permissions to chosen related objects (foreign keys
        and many to many) - the same as in admin forms.
        """
        model = self._meta.model
        for field in self.get_import_fields():
            if not field.attribute or field.readonly or field.column_name not in row:
                continue
            model_field = _get_model_field(model, field.attribute.split(LOOKUP_SEP)[0])
            related_model = getattr(model_field, "related_model", None)
            if not (
                related_model
                and issubclass(related_model, (PermissionsForObjectMixin, Polymorphic))
            ):
                continue
            if model_field.many_to_many:
                values = field.clean(row) or []
            else:
                value = getattr(instance, model_field.name, None)
                values = [value] if value else []
            for obj in values:
                target = _get_concrete_object(obj)
                if isinstance(target, PermissionsForObjectMixin) and not (
                    target.has_permission_to_object(self._ralph_user)
                ):
                    raise PermissionDenied(
                        _("You don't have permissions to select this value: %(value)s")
                        % {"value": obj}
                    )

    def after_init_instance(self, instance, new, row, **kwargs):
        super().after_init_instance(instance, new, row, **kwargs)
        if not new:
            self._check_object_permission(instance)

    def before_save_instance(self, instance, row, **kwargs):
        super().before_save_instance(instance, row, **kwargs)
        self._check_related_objects_permissions(instance, row)

    def after_save_instance(self, instance, row, **kwargs):
        super().after_save_instance(instance, row, **kwargs)
        # check permissions after changes too (ex. changed region)
        self._check_object_permission(instance)


def restrict_resource_class(resource_class, user, action, exclude_fields=(), scope_filter=None):
    """
    Return subclass of `resource_class` containing only fields to which
    `user` has `action` (view for export, change for import) permission.
    Fields from `exclude_fields` are removed for every user.
    If `scope_filter` (`Q` object) is provided, import is limited to objects
    matching it (before and after changes).
    """
    model = resource_class._meta.model
    import_id_fields = set(resource_class._meta.import_id_fields or ())
    exclude_fields = set(exclude_fields)
    allowed = OrderedDict()
    forbidden_columns = set()
    for name, field in resource_class.fields.items():
        attribute = _get_permission_attribute(resource_class, name, field)
        excluded = name in exclude_fields or attribute.split(LOOKUP_SEP)[0] in exclude_fields
        if not excluded and (
            user.is_superuser
            or model is None
            or name in import_id_fields
            or has_access_to_attribute(model, attribute, user, action)
        ):
            allowed[name] = field
        elif not field.readonly:
            # readonly fields are ignored during import anyway (but they're
            # removed from resource to not show their values in import preview)
            forbidden_columns.add(field.column_name)

    allowed_names = set(allowed) | {field.column_name for field in allowed.values()}
    meta = copy(resource_class._meta)
    for option in ("fields", "export_order", "import_order"):
        value = getattr(meta, option, None)
        if value is not None:
            setattr(meta, option, tuple(f for f in value if f in allowed_names))

    attrs = {
        "__module__": resource_class.__module__,
        "__qualname__": resource_class.__qualname__,
        "fields": allowed,
        "_meta": meta,
        "_ralph_user": user,
        "_scope_filter": scope_filter,
        "_forbidden_import_columns": frozenset(forbidden_columns),
    }
    # `type.__new__` is used directly to not trigger resource metaclasses
    # again (fields are already computed)
    return type.__new__(
        type(resource_class),
        resource_class.__name__,
        (RestrictedResourceMixin, resource_class),
        attrs,
    )
