import operator

from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _


def get_perm_key(action, class_name, field_name):
    """
    Generate django permission code name.

    :Example:

        >> perm = get_perm_key('change', 'baseobject', 'remarks')
        change_baseobject_remarks_field

    :param action: Permission action (change/view)
    :type action: str
    :param class_name: Django model class name
    :type class_name: str
    :param field_name: Django model field name
    :type field_name: str

    :return: django permission code name
    :rtype: str
    """
    return '{}_{}_{}_field'.format(action, class_name, field_name)


class user_permission(object):  # noqa
    """
    Decorator for functions which should validate if user has all rights to
    access objects, which usually is validating if user attribute value is the
    same as object attribute value.

    Function, on which this decorator is user should return
    `django.db.models.Q` object.

    Example:
    >>> @user_permission
    ... def in_region(user):
    ...     return Q(region=user.region)

    Notice that such functions could be joined using logical operators
    (AND, OR). These operators will be used on results of calls to these
    function (Q objects).
    """

    def __init__(self, func=None, name=None):
        """

        """
        self.func = func
        if not name and func:
            name = func.__name__
        self.name = name

    def __call__(self, user, *, skip_superuser_rights=False):
        """
        Notice that `skip_superuser_rights` should always be passed as keyword
        argument.
        """
        if not user or (not skip_superuser_rights and user.is_superuser):
            return models.Q()
        kw = {}
        # pass skip_superuser_rights info to operators
        if self.func and getattr(self.func, '_is_operator', False):
            kw['skip_superuser_rights'] = skip_superuser_rights
        return self.func(user, **kw) if self.func else models.Q()

    def _apply_operator(self, other, operator_):
        """
        Apply passed operator (ex. and) on self and other `user_permission`
        function. This is lazy evaluation (similar to decorator), which would
        return another instance of `user_permission` with dynamic function
        `func` (which is applying operator on self and other) as called
        function.
        """
        def func(*args, **kwargs):
            return operator_(self(*args, **kwargs), other(*args, **kwargs))
        func._is_operator = True
        return type(self)(func, name='({}: {}, {})'.format(
            operator.__name__.rstrip('_').upper(),
            self,
            other
        ))

    def __and__(self, other):
        return self._apply_operator(other, operator.and_)

    def __or__(self, other):
        return self._apply_operator(other, operator.or_)

    def __repr__(self):
        return self.name or '<True>'


class PermissionsBase(ModelBase):

    """
    Metaclass extending django permissions:
    * adding django permissions based on all fields in the model
    * adding object-level permissions (checked for user)

    :Example:
        @user_permission
        def in_region(user):
            return Q(region=user.region)

        class Test(models.Model, metaclass=PermissionByFieldBase)):

            ...

            class Permissions:
                # Fields to exclude generated permissions
                blacklist = set(['sample_field'])
                # object-level permissions
                has_access = in_region
    """

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        permissions = attrs.pop('Permissions', None)
        if not permissions:
            permissions = getattr(
                new_class,
                'Permissions',
                type(str('Permissions'), (object,), dict())
            )
        permissions.blacklist = cls._init_blacklist(cls, permissions, bases)
        permissions.has_access = cls._init_object_permissions(
            cls, permissions, bases
        )
        new_class.add_to_class('_permissions', permissions)
        cls._init_meta_permissions(cls, new_class)
        return new_class

    def _init_blacklist(cls, permissions, bases):
        blacklist = getattr(permissions, 'blacklist', set())
        for base in bases:
            try:
                blacklist |= base.Permissions.blacklist
            except AttributeError:
                pass
        return blacklist

    def _init_meta_permissions(cls, new_class):
        class_name = new_class._meta.model_name
        model_fields = new_class._meta.fields
        for field in model_fields:
            name = field.name
            if (
                not field.primary_key and
                name not in new_class._permissions.blacklist
            ):
                new_class._meta.permissions.append((
                    get_perm_key('change', class_name, name),
                    _('Can change {} field').format(field.verbose_name)
                ))
                new_class._meta.permissions.append((
                    get_perm_key('view', class_name, name),
                    _('Can view {} field').format(field.verbose_name)
                ))

    def _init_object_permissions(cls, permissions, bases):
        has_access = getattr(permissions, 'has_access', user_permission())
        for base in bases:
            try:
                has_access &= base.Permissions.has_access
            except AttributeError:
                pass
        return has_access


class PermByFieldMixin(models.Model, metaclass=PermissionsBase):

    """Django Abstract model class for permission by fields."""

    @classmethod
    def has_access_to_field(cls, field_name, user, action='change'):
        """
        Checks the user has the permission to the field

        :Example:

            >> user = User.objects.get(username='root')
            >> model.has_access_to_field('remarks', user, action='change')
            True

        :param field_name: django model field name
        :type field_name: str
        :param user: User object
        :type user: django User object
        :param action: permission action (change/view)
        :type action: str

        :return: True or False
        :rtype: bool
        """
        perm_key = get_perm_key(
            action,
            cls._meta.model_name,
            field_name
        )
        perm = user.has_perm(
            '{}.{}'.format(cls._meta.app_label, perm_key)
        )
        # If the user does not have rights to view,
        # but has the right to change he can view the field
        if action == 'view' and not perm:
            perm_key = get_perm_key(
                'change',
                cls._meta.model_name,
                field_name
            )
            perm = user.has_perm(
                '{}.{}'.format(cls._meta.app_label, perm_key)
            )
        return perm

    @classmethod
    def allowed_fields(cls, user, action='change'):
        """
        Returns a list with the names of the fields to which the user has
        permission.

        :Example:

            >> user = User.objects.get(username='root')
            >> model.allowed_fields(user, 'change')
            ['parent', 'remarks', 'service_env']

        :param user: User object
        :type user: django User object
        :param action: permission action (change/view)
        :type action: str

        :return: List of field names
        :rtype: list
        """
        result = []
        blacklist = cls._permissions.blacklist

        for field in cls._meta.fields:
            if (
                not field.primary_key and
                field.name not in blacklist and
                cls.has_access_to_field(field.name, user, action)
            ):
                result.append(field.name)

        return set(result)

    class Meta:
        abstract = True


class PermissionsForObjectMixin(models.Model, metaclass=PermissionsBase):
    """Django Abstract model class for object-level permissions."""

    def has_permission_to_object(self, user):
        """
        Check if user has all rights to single object.
        """
        return self._default_manager.filter(
            self._permissions.has_access(user),
            pk=self.pk
        ).exists()

    @classmethod
    def _get_objects_for_user(cls, user, queryset=None):
        """
        Return objects (as queryset) to which user has access.

        :rtype: `django.db.models.QuerySet`
        """
        if queryset is None:
            queryset = cls._default_manager
        return queryset.filter(cls._permissions.has_access(user))

    class Meta:
        abstract = True
