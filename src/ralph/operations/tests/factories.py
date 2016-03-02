# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

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


class OperationFactory(DjangoModelFactory):

    title = factory.Sequence(lambda n: 'Operation #%d' % n)
    status = OperationStatus.opened
    type = factory.LazyAttribute(lambda obj: get_operation_type('Change'))

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
