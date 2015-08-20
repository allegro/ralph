# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from rest_framework import permissions, routers, serializers, viewsets

from ralph.lib.permissions.api import (
    ObjectPermissionsMixin,
    PermissionsForObjectFilter,
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin
)
from ralph.lib.permissions.tests.models import Article, Library, LongArticle


class Permission(ObjectPermissionsMixin, permissions.IsAuthenticated):
    pass


class ArticleSerializer(
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = Article


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [PermissionsForObjectFilter]
    permission_classes = [Permission]


class LongArticleSerializer(
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = LongArticle


class LongArticleViewSet(viewsets.ModelViewSet):
    queryset = LongArticle.objects.all()
    serializer_class = LongArticleSerializer
    filter_backends = [PermissionsForObjectFilter]
    permission_classes = [Permission]


class LibrarySerializer(
    PermissionsPerFieldSerializerMixin,
    RelatedObjectsPermissionsSerializerMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = Library


class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer


router = routers.DefaultRouter()
router.register(r'articles', ArticleViewSet)
router.register(r'long-articles', LongArticleViewSet)
router.register(r'library', LibraryViewSet)
urlpatterns = [
    url(r'^test-api/', include(router.urls, namespace='test-api')),
]
