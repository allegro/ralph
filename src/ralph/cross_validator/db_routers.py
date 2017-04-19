class CrossRouter(object):
    def db_for_read(self, model, **hints):
        if hasattr(model, 'i_am_your_father'):
            return 'default'

        if model._meta.app_label == 'cross_validator':
            return 'ralph2'
        return 'ralph3'

    def db_for_write(self, model, **hints):
        if hasattr(model, 'i_am_your_father'):
            return 'default'
        return None
