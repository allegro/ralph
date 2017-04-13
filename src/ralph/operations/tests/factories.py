# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from ralph.accounts.tests.factories import UserFactory
from ralph.operations.models import (
    Change,
    Failure,
    Incident,
    Operation,
    OperationStatus,
    OperationType,
    Problem
)


def get_operation_type(name):
    return OperationType.objects.get(name=name)


def get_operation_status(name):
    return OperationStatus.objects.get(name=name)


class OperationTypeFactory(DjangoModelFactory):

    name = factory.Iterator(['Problem', 'Incident', 'Failure', 'Change'])

    class Meta:
        model = OperationType
        django_get_or_create = ['name']


class OperationStatusFactory(DjangoModelFactory):

    name = factory.Iterator(['Open', 'Closed', 'Resolved', 'In Progress'])

    class Meta:
        model = OperationStatus
        django_get_or_create = ['name']


class OperationFactory(DjangoModelFactory):

    title = factory.Sequence(lambda n: 'Operation #%d' % n)
    status = factory.LazyAttribute(lambda obj: get_operation_status('Open'))
    type = factory.LazyAttribute(lambda obj: get_operation_type('Change'))
    assignee = factory.SubFactory(UserFactory)

    class Meta:
        model = Operation


class ChangeFactory(OperationFactory):
    class Meta:
        model = Change


class FailureFactory(OperationFactory):
    type = factory.LazyAttribute(lambda obj: get_operation_type('Failure'))

    class Meta:
        model = Failure


class ProblemFactory(OperationFactory):
    type = factory.LazyAttribute(lambda obj: get_operation_type('Problem'))

    class Meta:
        model = Problem


class IncidentFactory(OperationFactory):
    type = factory.LazyAttribute(lambda obj: get_operation_type('Incident'))

    class Meta:
        model = Incident
