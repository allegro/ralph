from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _
from six import with_metaclass


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


class PermissionByFieldBase(ModelBase):

    """
    Metaclass adding django permissions based on all fields in the model.

    :Example:

        class Test(with_metaclass(PermissionByFieldBase, models.Model)):

            ...

            class Permissions:
                # Fields to exclude generated permissions
                blacklist = set(['sample_field'])
    """

    def __new__(cls, name, bases, attrs):
        new_class = super(PermissionByFieldBase, cls).__new__(
            cls, name, bases, attrs
        )
        class_name = new_class._meta.model_name
        model_fields = new_class._meta.fields

        permissions = attrs.pop('Permissions', None)
        if not permissions:
            permissions = getattr(
                new_class,
                'Permissions',
                type(str('Permissions'), (object,), dict())
            )

        blacklist = getattr(permissions, 'blacklist', set())
        for base in bases:
            try:
                blacklist |= base.Permissions.blacklist
            except AttributeError:
                pass

        permissions.blacklist = blacklist

        new_class.add_to_class('_permissions', permissions)

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

        return new_class


class PermByFieldMixin(with_metaclass(PermissionByFieldBase, models.Model)):

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
        return user.has_perm(
            '{}.{}'.format(cls._meta.app_label, perm_key)
        )

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
