#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import (
    ComponentModel,
    ComponentModelGroup,
    ComponentType,
    Device,
    Memory,
    Processor,
    Storage
)


def duplicate_item(item):
    return [item] * item.get('count')


def create_model(device, mdl, type):
    group, created = ComponentModelGroup.objects.get_or_create(
        name='Group %s - %s' % (mdl.get('model_name'), mdl.get('price')),
        price=mdl.get('price'),
        type=type,
    )
    if type == ComponentType.memory:
        model, created = ComponentModel.objects.get_or_create(
            name='Model %s %s' % (mdl.get('family'), mdl.get('size')),
            group=group,
            family=mdl.get('family'),
            speed=mdl.get('speed'),
            size=mdl.get('size'),
            type=ComponentType.memory,
        )
    elif type == ComponentType.processor:
        model, created = ComponentModel.objects.get_or_create(
            name='M %s - %s' % (
                mdl.get('model_name'), mdl.get('price')
            ),
            group=group,
            family=mdl.get('family'),
            type=type,
            speed=mdl.get('speed'),
        )
    else:
        model, created = ComponentModel.objects.get_or_create(
            name='M %s - %s' % (
                mdl.get('model_name'),
                mdl.get('price'),
            ),
            group=group,
            family=mdl.get('family'),
            type=type,
        )
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
        deprecation_kind=device.get('deprecation_kind'),
        purchase_date=device.get('purchase_date'),
    )
    dev.name = device.get('name')
    dev.save()
    if cpu:
        model = create_model(device, cpu, ComponentType.processor)
        for cpu in duplicate_item(cpu):
            Processor(
                device=dev,
                model=model,
                label=cpu.get('label'),
            ).save()
    if memory:
        model = create_model(device, memory, ComponentType.memory)
        for memory in duplicate_item(memory):
            Memory(
                device=dev,
                model=model,
                speed=memory.get('speed'),
                size=memory.get('size'),
                label=memory.get('label'),
            ).save()
    if storage:
        model = create_model(device, storage, ComponentType.disk)
        for storage in duplicate_item(storage):
            Storage(
                device=dev,
                model=model,
                label=storage.get('label'),
            ).save()
    return dev
