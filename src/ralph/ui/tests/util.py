#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery.models import Device

def create_device(device, cpu=None, memory=None, storage=None):
	dev = Device.create(
		model=device.get('model'),
		model_name=device.get('model_name'),
		model_type=device.get('model_type'),
		sn=device.get('sn'),
		venture=device.get('venture'),
		parent=device.get('parent'),
		price=device.get('price')
	)
	dev.name = device.get('name')
	dev.save()

	if cpu:
		pass
	if memory:
		pass
	if storage:
		pass

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
