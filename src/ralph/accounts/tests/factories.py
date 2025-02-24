# -*- coding: utf-8 -*-
import factory
from django.contrib.auth.models import Group
from factory.django import DjangoModelFactory

from ralph.accounts.models import RalphUser, Region, Team


class RegionFactory(DjangoModelFactory):
    name = factory.Iterator(["pl", "de", "ua"])

    class Meta:
        model = Region
        django_get_or_create = ["name"]


class GroupFactory(DjangoModelFactory):
    name = factory.Iterator(["DBA", "sysadmins", "devops"])

    class Meta:
        model = Group
        django_get_or_create = ["name"]


class UserFactory(DjangoModelFactory):
    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True

    class Meta:
        model = RalphUser
        django_get_or_create = ["username"]

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            extracted = [GroupFactory() for i in range(2)]

        if extracted:
            for group in extracted:
                self.groups.add(group)


class TeamFactory(DjangoModelFactory):
    name = factory.Iterator(["DBA", "sysadmins", "devops"])

    class Meta:
        model = Team
        django_get_or_create = ["name"]
