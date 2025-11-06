# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connections, DEFAULT_DB_ALIAS
from django.test.utils import CaptureQueriesContext  # noqa
from rest_framework.test import APITestCase

from ralph.tests.models import Foo


class APIPermissionsTestMixin(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.foo = Foo.objects.create(bar="rab")

        def create_user(name, **kwargs):
            params = dict(
                username=name,
                is_staff=True,
                is_active=True,
            )
            params.update(kwargs)
            return get_user_model().objects.create(**params)

        cls.user1 = create_user("user1")
        cls.user2 = create_user("user2")
        cls.user3 = create_user("user3")
        cls.user_not_staff = create_user("user_not_staff", is_staff=False)

        def add_perm(user, perm):
            user.user_permissions.add(
                Permission.objects.get(
                    content_type=ContentType.objects.get_for_model(Foo), codename=perm
                )
            )

        add_perm(cls.user1, "change_foo")
        add_perm(cls.user1, "delete_foo")
        add_perm(cls.user2, "add_foo")
        add_perm(cls.user_not_staff, "change_foo")


class _AssertNumQueriesMoreOrLessContext(CaptureQueriesContext):
    def __init__(self, test_case, number, plus_minus, connection):
        self.test_case = test_case
        self.range = range(number - plus_minus, number + plus_minus + 1)
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        executed = len(self)
        self.test_case.assertIn(
            executed,
            self.range,
            "%d queries executed, %s expected\nCaptured queries were:\n%s"
            % (
                executed,
                self.range,
                "\n".join(
                    "%d. %s" % (i, query["sql"])
                    for i, query in enumerate(self.captured_queries, start=1)
                ),
            ),
        )


class RalphAPITestCase(APITestCase):
    """
    Base test for Ralph API Test Case.

    By default there are some users created.
    """

    @classmethod
    def _create_users(cls):
        def create_user(name, **kwargs):
            params = dict(
                username=name,
                is_staff=True,
                is_active=True,
            )
            params.update(kwargs)
            return get_user_model().objects.create(**params)

        cls.user1 = create_user("user1")
        cls.user2 = create_user("user2")
        cls.superuser = create_user("superuser", is_staff=True, is_superuser=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_users()

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.superuser)

    @classmethod
    def get_full_url(self, url):
        """
        Convert URL to fully qualified URL (with protocol and domain).
        """
        # testserver is default name of server using by Django test client
        # see django/test/client.py for details
        return "http://testserver{}".format(url)

    def assertQueriesMoreOrLess(
        self,
        number: int,
        plus_minus: int,
        func=None,
        *args,
        using=DEFAULT_DB_ALIAS,
        **kwargs,
    ):
        conn = connections[using]

        context = _AssertNumQueriesMoreOrLessContext(self, number, plus_minus, conn)
        if func is None:
            return context

        with context:
            func(*args, **kwargs)
