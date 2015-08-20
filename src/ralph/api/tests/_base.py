# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from ralph.tests.models import Foo


class APIPermissionsTestMixin(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.foo = Foo.objects.create(bar='rab')

        def create_user(name, **kwargs):
            params = dict(
                username=name,
                is_staff=True,
                is_active=True,
            )
            params.update(kwargs)
            return get_user_model().objects.create(**params)
        cls.user1 = create_user('user1')
        cls.user2 = create_user('user2')
        cls.user3 = create_user('user3')
        cls.user_not_staff = create_user('user_not_staff', is_staff=False)

        def add_perm(user, perm):
            user.user_permissions.add(Permission.objects.get(
                content_type=ContentType.objects.get_for_model(Foo),
                codename=perm
            ))
        add_perm(cls.user1, 'change_foo')
        add_perm(cls.user1, 'delete_foo')
        add_perm(cls.user2, 'add_foo')
        add_perm(cls.user_not_staff, 'change_foo')
