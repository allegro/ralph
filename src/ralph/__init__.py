from django.db.models.options import Options

__version__ = "3.0.0"


def monkey_options_init(self, meta, app_label):
    self._old__init__(meta, app_label)
    self.default_permissions = ("add", "change", "delete", "view")


Options._old__init__ = Options.__init__
Options.__init__ = lambda self, meta, app_label=None: monkey_options_init(
    self, meta, app_label
)
