from django.conf import settings
from django.db import models

from ralph.lib.permissions.models import (
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


class Article(PermissionsForObjectMixin, models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=1000)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL)

    class Permissions:
        has_access = is_author | is_collabolator

    def __str__(self):
        return self.title


class LongArticle(Article):
    remarks = models.CharField(max_length=100)

    class Permissions:
        # notice that this permission is anded (&) with Article permissions
        has_access = has_long_title


class Library(models.Model):
    lead_article = models.ForeignKey(Article)
    articles = models.ManyToManyField(Article)
