# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db

from lck.django.common.models import Named, WithConcurrentGetOrCreate
from lck.django.choices import Choices


class PricingAggregate(Choices):
    """The way to aggregate values of a variable."""

    _ = Choices.Choice

    sum = _("Sum") << {'function': db.Sum}
    average = _("Average") << {'function': db.Avg}
    min = _("Minimum") << {'function': db.Min}
    max = _("Maximum") << {'function': db.Max}


class PricingGroup(db.Model):
    """A group of devices that are priced according to common rules for the given month."""

    name = db.CharField(max_length=64)
    devices = db.ManyToManyField('discovery.Device')
    date = db.DateField()


class PricingFormula(db.Model, WithConcurrentGetOrCreate):
    """
    A formula for pricing a specific component in a specific pricing group.
    """
    group = db.ForeignKey('discovery.PricingGroup')
    component_group = db.ForeignKey('discovery.ComponentModelGroup')
    formula = db.CharField(max_length=255)


class PricingVariable(Named):
    """
    A variable that is used in the pricing formulas.
    """
    group = db.ForeignKey('discovery.PricingGroup')
    aggregate = db.PositiveIntegerField(
        choices=PricingAggregate(),
        default=PricingAggregate.sum,
    )

    def get_value(self):
        function = self.aggregate.function
        d = self.pricingvalue_set.aggregate(function('value'))
        return d.values()[0]


class PricingValue(db.Model):
    """
    A value of a variable that is used in the pricing formulas.
    """
    device = db.ForeignKey('discovery.Device')
    variable =  db.ForeignKey('discovery.PricingVariable')
    value = db.DecimalField()

