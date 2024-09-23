from django.conf.urls import include, url
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.views.generic import View

from ralph.lib.permissions.views import PermissionViewMetaClass


class SimplePermissionView(View, metaclass=PermissionViewMetaClass):

    """Simple Django generic views class for permission view test."""

    def get(self, request):
        return HttpResponse('ok')


urls = [url(
    r'^test-view-permissions/',
    SimplePermissionView.as_view(),
    name='test-view-permissions'
)]


class PermissionsByFieldTestCase(TestCase):
    def setUp(self):
        self.codename = 'can_view_extra_simplepermissionview'
        self.user_not_perm = get_user_model().objects.create_user(
            username='user_not_perm',
            password='password',
        )
        self.user_with_perm = get_user_model().objects.create_user(
            username='user_with_perm',
            password='password',
        )
        self.user_with_perm.user_permissions.add(
            Permission.objects.get(codename=self.codename)
        )
        self.root = get_user_model().objects.create_superuser(
            username='root',
            password='password',
            email='email@email.pl'
        )
        self.url = reverse('test-view-permissions')

    def test_codename(self):
        self.assertEqual(
            SimplePermissionView.permision_codename,
            self.codename
        )

    def test_user_not_perm(self):
        self.client.login(
            username=self.user_not_perm.username, password='password'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_user_with_perm(self):
        self.client.login(
            username=self.user_with_perm.username, password='password'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_user_root(self):
        self.client.login(
            username=self.root.username, password='password'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
