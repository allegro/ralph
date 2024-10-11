# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models

from ralph.lib.permissions.models import (
    PermByFieldMixin,
    PermissionsForObjectMixin,
    user_permission
)


@user_permission
def is_author(user):
    return models.Q(author=user)


@user_permission
def is_collabolator(user):
    return models.Q(collaborators=user)


@user_permission
def has_long_title(user):
    return models.Q(title__regex=r'.{10}.*')


class Article(PermByFieldMixin, PermissionsForObjectMixin, models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='articles_author', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=1000)
    custom_field_1 = models.CharField(max_length=100, null=True, blank=True)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='articles_collaborator')

    class Permissions:
        has_access = is_author | is_collabolator

    def __str__(self):
        return self.title

    def sample_non_model_field(self):
        return '123'

    def sample_non_model_field_with_permissions(self):
        return '321'
    sample_non_model_field_with_permissions._permission_field = 'content'

    @property
    def sample_property(self):
        return 'xyz'

    @property
    def sample_property_with_permissions(self):
        return 'zyx'


class LongArticle(Article):
    remarks = models.CharField(max_length=100)
    custom_field_2 = models.ForeignKey(
        Article,
        null=True,
        blank=True,
        related_name='long_article',
        on_delete=models.CASCADE
    )

    class Permissions:
        # notice that this permission is anded (&) with Article permissions
        has_access = has_long_title


class Library(models.Model):
    lead_article = models.ForeignKey(Article, related_name='library_lead', on_delete=models.CASCADE)
    articles = models.ManyToManyField(Article, related_name='library_articles')


class Foo(models.Model):
    bar = models.CharField('bar', max_length=50)
