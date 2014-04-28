#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pkgutil
import importlib


for loader, name, ispkg in pkgutil.iter_modules(__path__, __name__ + '.'):
    importlib.import_module(name)
