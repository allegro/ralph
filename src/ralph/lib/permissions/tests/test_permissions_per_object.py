# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase

from ralph.lib.permissions.admin import PermissionsPerObjectFormMixin
from ralph.lib.permissions.tests._base import PermissionsTestMixin
from ralph.lib.permissions.tests.models import (
    Article,
    has_long_title,
    is_author,
    is_collabolator,
    Library,
    LongArticle
)


class TestUserPermissions(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(username='user1')
        self.superuser = get_user_model().objects.create(
            username='superuser', is_superuser=True
        )

    def test_is_author(self):
        result = is_author(self.user1)
        self.assertEqual(
            str(result),
            "(AND: ('author', {u}))".format(u=repr(self.user1))
        )

    def test_is_author_and_collaborator(self):
        result = (is_author & is_collabolator)(self.user1)
        self.assertEqual(
            str(result),
            "(AND: ('author', {u}), ('collaborators', {u}))".format(
                u=repr(self.user1)
            )
        )

    def test_is_author_or_collaborator(self):
        result = (is_author | is_collabolator)(self.user1)
        self.assertEqual(
            str(result),
            "(OR: ('author', {u}), ('collaborators', {u}))".format(
                u=repr(self.user1)
            )
        )

    def test_is_author_or_collaborator_and_has_long_title(self):
        result = ((is_author | is_collabolator) & has_long_title)(self.user1)
        self.assertEqual(
            str(result),
            (
                "(AND: (OR: ('author', {u}), ('collaborators', {u})), "
                "('title__regex', '.{{10}}.*'))"
            ).format(u=repr(self.user1))
        )

    def test_is_author_or_collaborator_when_superuser(self):
        result = (is_author | is_collabolator)(self.superuser)
        self.assertEqual(str(result), "(AND: )")

    def test_is_author_or_collaborator_when_superuser_and_skip_superuser_rights(self):  # noqa
        result = (is_author | is_collabolator)(
            self.superuser, skip_superuser_rights=True
        )
        self.assertEqual(
            str(result),
            "(OR: ('author', {u}), ('collaborators', {u}))".format(
                u=repr(self.superuser)
            )
        )


@ddt
class TestPermissionsPerObject(PermissionsTestMixin, TestCase):
    def setUp(self):
        self._create_users_and_articles()

    def test_author_should_have_access_to_his_article(self):
        self.assertTrue(
            self.article_2.has_permission_to_object(self.user2)
        )

    def test_superuser_should_have_access_to_any_article(self):
        self.assertTrue(
            self.article_1.has_permission_to_object(self.superuser)
        )

    def test_collabolator_should_have_access_to_his_article(self):
        self.assertTrue(self.article_1.has_permission_to_object(self.user2))

    def test_user_should_not_have_access_to_not_his_artictle(self):
        # article without collaborators
        self.assertFalse(
            self.article_2.has_permission_to_object(self.user3)
        )
        # article with collaborators
        self.assertFalse(
            self.article_1.has_permission_to_object(self.user3)
        )

    def test_superuser_should_have_access_to_any_long_article(self):
        self.assertTrue(
            self.long_article.has_permission_to_object(self.superuser)
        )

    def test_author_should_have_access_to_long_article_when_it_is_long(self):
        self.assertTrue(
            self.long_article.has_permission_to_object(self.user1)
        )

    def test_author_should_not_have_access_to_long_article_when_it_is_not_long(self):  # noqa
        self.assertFalse(
            self.long_article_2.has_permission_to_object(self.user1)
        )

    @unpack
    @data(
        # single Article + 2x LongArticle (notice that LongArticle permissions
        # are not respected here!)
        (Article, 'user1', 3),
        (Article, 'user2', 2),
        (LongArticle, 'user1', 1),
        (LongArticle, 'user2', 0),
    )
    def test_get_objects_for_user(self, article_cls, username, count):
        self.assertEqual(
            article_cls._get_objects_for_user(getattr(self, username)).count(),
            count
        )

    def test_get_object_for_superuser(self):
        self.assertEqual(
            Article._get_objects_for_user(self.superuser).count(),
            Article.objects.count()
        )
        self.assertEqual(
            LongArticle._get_objects_for_user(self.superuser).count(),
            LongArticle.objects.count()
        )


class TestPermissionsPerObjectForm(PermissionsTestMixin, TestCase):
    class SampleForm(PermissionsPerObjectFormMixin, forms.ModelForm):
        class Meta:
            model = Library
            exclude = []

    def setUp(self):
        self._create_users_and_articles()

    def test_save_valid_foreign_key_should_pass(self):
        form = self.SampleForm({
            'lead_article': self.article_1.id,
            'articles': [self.long_article.id]
        }, _user=self.user1)
        self.assertTrue(form.is_valid())

    def test_save_invalid_foreign_key_should_have_form_errors(self):
        form = self.SampleForm({
            'lead_article': self.article_2.id,
            'articles': [self.long_article.id]
        }, _user=self.user1)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'lead_article': ["You don't have permissions to select this value"]
        })

    def test_save_invalid_m2m_should_have_form_errors(self):
        form = self.SampleForm({
            'lead_article': self.article_1.id,
            'articles': [self.long_article_2.id]
        }, _user=self.user2)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'articles': ["You don't have permissions to select this value"]
        })
