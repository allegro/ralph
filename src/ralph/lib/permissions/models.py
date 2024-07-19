import operator

from django.contrib.auth.management import _get_all_permissions
from django.core import exceptions
from django.db import DEFAULT_DB_ALIAS, models, router, transaction
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
            operator_.__name__.rstrip('_').upper(),
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
        apply_bases_permissions = True
        if not permissions:
            # apply bases permissions only if there are new permissions in
            # new class
            apply_bases_permissions = False
            permissions = getattr(
                new_class,
                'Permissions',
                type(str('Permissions'), (object,), dict())
            )
        permissions.blacklist = cls._init_blacklist(cls, permissions, bases)
        permissions.has_access = cls._init_object_permissions(
            cls, permissions, bases, apply_bases_permissions
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
        model_fields = (
            new_class._meta.fields +
            new_class._meta.many_to_many
        )
        for field in model_fields:
            name = field.name
            if name in new_class._permissions.blacklist:
                continue
            new_class._meta.permissions.append((
                get_perm_key('view', class_name, name),
                _('Can view {} field').format(field.verbose_name)
            ))
            if field.primary_key:
                continue
            new_class._meta.permissions.append((
                get_perm_key('change', class_name, name),
                _('Can change {} field').format(field.verbose_name)
            ))

    def _init_object_permissions(cls, permissions, bases, apply_bases=True):
        has_access = getattr(permissions, 'has_access', user_permission())
        if apply_bases:
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
        # TODO: if it's m2m field, check on the other side
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
            return cls.has_access_to_field(field_name, user, action='change')
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
        result = set()
        blacklist = cls._permissions.blacklist

        for field in (cls._meta.fields + cls._meta.many_to_many):
            if (
                field.name not in blacklist and
                cls.has_access_to_field(field.name, user, action)
            ):
                result.add(field.name)
        # If the user does not have rights to view,
        # but has the right to change he can view the field
        if action == 'view':
            result |= cls.allowed_fields(user, 'change')
        return result

    class Meta:
        abstract = True


class PermissionsForObjectMixin(models.Model, metaclass=PermissionsBase):
    """Django Abstract model class for object-level permissions."""

    def has_permission_to_object(self, user):
        """
        Check if user has all rights to single object.
        """
        user_perms = self._permissions.has_access(user)
        if not user_perms:
            return True
        return self.__class__.objects.filter(
            user_perms,
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


@transaction.atomic
def create_permissions(
    app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, **kwargs
):
    """
    Copy/paste from django/contrib/auth/management/__init__.py with
    small modifications (for_concrete_model, app_config.get_proxies).

    Create permissions for defined proxy models in apps module.
    """
    from django.apps import apps

    if not app_config.models_module:
        return

    try:
        Permission = apps.get_model('auth', 'Permission')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    from django.contrib.contenttypes.models import ContentType

    # This will hold the permissions we're looking for as
    # (content_type, (codename, name))
    searched_perms = list()
    # The codenames and ctypes that should exist.
    ctypes = set()
    for klass in app_config.get_models():
        # Force looking up the content types in the current database
        # before creating foreign keys to them.
        ctype = ContentType.objects.db_manager(using).get_for_model(
            model=klass, for_concrete_model=False
        )
        if klass._meta.proxy:
            concrete_ctype = ContentType.objects.db_manager(using).get_for_model(  # noqa
                model=klass,
            )
            perms = Permission.objects.using(using).filter(
                content_type=concrete_ctype,
                codename__endswith=klass._meta.model_name
            )
            if perms:
                perms.update(content_type=ctype)
        ctypes.add(ctype)
        for perm in _get_all_permissions(klass._meta):
            searched_perms.append((ctype, perm))

    # Find all the Permissions that have a content_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(Permission.objects.using(using).filter(
        content_type__in=ctypes,
    ).values_list(
        "content_type", "codename"
    ))

    perms = [
        Permission(codename=codename, name=name, content_type=ct)
        for ct, (codename, name) in searched_perms
        if (ct.pk, codename) not in all_perms
    ]
    # Validate the permissions before bulk_creation to avoid cryptic
    # database error when the verbose_name is longer than 50 characters
    permission_name_max_length = Permission._meta.get_field('name').max_length
    verbose_name_max_length = permission_name_max_length - len('Can change ')
    for perm in perms:
        if len(perm.name) > permission_name_max_length:
            raise exceptions.ValidationError(
                "The verbose_name of %s.%s is longer than %s characters" % (
                    perm.content_type.app_label,
                    perm.content_type.model,
                    verbose_name_max_length,
                )
            )
    Permission.objects.using(using).bulk_create(perms)
    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s'" % perm)
