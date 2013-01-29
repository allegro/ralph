#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import (
    Device, Processor, ComponentModel, ComponentModelGroup, ComponentType,
    Memory, Storage
)


def dublicate_item(item):
    duplicate = []
    for component in range(item.get('count')):
        duplicate.append(item)
    return duplicate


def create_model(device, mdl, type):
    try:
        group = ComponentModelGroup.objects.get(
            name='Group %s' % mdl.get('model_name')
        )
    except ComponentModelGroup.DoesNotExist:
        group = ComponentModelGroup(
            name='Group %s' % mdl.get('model_name'),
            price=mdl.get('price'),
            type=type
        ).save()
    try:
        model = ComponentModel.objects.get(
            family=mdl.get('family')
        )
    except ComponentModel.DoesNotExist:
        if type == ComponentType.memory:
            model = ComponentModel(
                name='Model %s %s' % (mdl.get('family'), mdl.get('size')),
                group=group,
                family=mdl.get('family'),
                speed=mdl.get('speed'),
                size=mdl.get('size')
            ).save()
        else:
            model = ComponentModel(
                name=mdl.get('model_name'),
                group=group,
                family=mdl.get('family')
            ).save()
    return model


def create_device(device, cpu=None, memory=None, storage=None):
    dev = Device.create(
        model=device.get('model'),
        model_name=device.get('model_name'),
        model_type=device.get('model_type'),
        sn=device.get('sn'),
        venture=device.get('venture'),
        parent=device.get('parent'),
        price=device.get('price'),
        deprecation_kind=device.get('deprecation_kind')
    )
    dev.name = device.get('name')
    dev.save()
    if cpu:
        model = create_model(device, cpu, ComponentType.processor)
        for cpu in dublicate_item(cpu):
            Processor(
                device=dev,
                model=model,
                label=cpu.get('label')
            ).save()
    if memory:
        model = create_model(device, memory, ComponentType.memory)
        for memory in dublicate_item(memory):
            Memory(
                device=dev,
                model=model,
                speed=memory.get('speed'),
                size=memory.get('size'),
                label=memory.get('label')
            ).save()
    if storage:
        model = create_model(device, storage, ComponentType.disk)
        for storage in dublicate_item(storage):
            Storage(
                device=dev,
                model=model,
                label=storage.get('label')
            ).save()


def sum_for_view(device):
    sum_dev = 0
    price = device.get('price')
    count = 0
    total_component = 0
    components = device.get('component')
    if components:
        for component in components:
            count = component.get('count')
            total_component = component.get('total_component')
            sum_dev += total_component
    return count, price, total_component, sum_dev
