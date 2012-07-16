# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

class PowerDNSRouter(object):
    """Route all operations on the powerdns models to the powerdns database."""

    db_name = 'powerdns'
    app_name = 'powerdns'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_name:
            return self.db_name
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_name:
            return self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (obj1._meta.app_label == self.app_name and
            obj2._meta.app_label == self.app_name):
            return True
        return None

    def allow_syncdb(self, db, model):
        if model._meta.app_label == self.app_name:
            return db == self.db_name
        elif db == self.db_name:
            return False
        return None
