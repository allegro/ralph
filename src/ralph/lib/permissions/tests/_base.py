# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from ralph.lib.permissions.tests.models import Article, Library, LongArticle


class PermissionsTestMixin(object):
    def _create_users_and_articles(self):
        self.user1 = get_user_model().objects.create(username='user1')
        self.user2 = get_user_model().objects.create(username='user2')
        self.user3 = get_user_model().objects.create(username='user3')
        self.superuser = get_user_model().objects.create(
            username='superuser', is_superuser=True
        )

        content_types = [ContentType.objects.get_for_model(m) for m in (
            Article,
            LongArticle,
            Library,
        )]
        base_permissions = Permission.objects.filter(
            content_type__in=content_types
        )
        for user in (self.user1, self.user2, self.user3):
            user.user_permissions.add(*base_permissions)

        # remove some permissions:
        # user1 doesn't have access to custome_field_1 at all
        self.user1.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_custom_field_1_field'
        ))
        self.user1.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='view_article_custom_field_1_field'
        ))
        # user3 doesn't have change permissions on custom_field_1
        self.user3.user_permissions.remove(Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Article),
            codename='change_article_custom_field_1_field'
        ))

        # create two articles for each user
        self.article_1 = Article.objects.create(
            author=self.user1,
            title='1',
            content='1'*10,
            custom_field_1='test value',
        )
        self.article_2 = Article.objects.create(
            author=self.user2,
            title='2',
            content='2'*10,
        )
        self.article_3 = Article.objects.create(
            author=self.user3,
            title='3',
            content='3'*10,
            custom_field_1='test value 2',
        )

        # create group article
        self.article_1.collaborators.add(self.user2)

        # create article with long title
        self.long_article = LongArticle.objects.create(
            author=self.user1,
            title='####### long article ########',
            content='lorem ipsum',
            custom_field_1='ipsum lorem',
        )
        self.long_article_2 = LongArticle.objects.create(
            author=self.user1,
            title='short',
            content='lorem ipsum',
            custom_field_2=self.article_1,
        )
