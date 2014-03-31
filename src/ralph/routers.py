# -*- coding: utf-8 -*-


class BaseRouter(object):

    """Route all operations on models to the ralph database."""

    # specify db_name and app_name in the
    db_name = ''
    app_name = ''

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
            # workaround for http://south.aeracode.org/ticket/370
            return model._meta.app_label == 'south'
        return None


class RalphRouter(BaseRouter):
    db_name = 'ralph'
    app_name = 'ralph'
