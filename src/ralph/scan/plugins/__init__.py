# -*- coding: utf-8 -*-

import pkgutil


for loader, name, ispkg in pkgutil.iter_modules(__path__, __name__ + '.'):
    __import__(name, globals(), locals(), [], -1)
