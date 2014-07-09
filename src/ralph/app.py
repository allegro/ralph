"""Ralph extension for DjangoPluggableApp."""

import abc
import pluggableapp


class RalphModule(pluggableapp.PluggableApp):

    """A pluggable application that depends of ralph and is accessible from
    the ralph main application."""

    metaclass = abc.ABCMeta
    required_permission = None

    @abc.abstractproperty
    def url_prefix(self):
        """The first part of paths for this application."""

    @abc.abstractproperty
    def module_name(self):
        """The name of the module for this application."""

    @abc.abstractproperty
    def icon(self):
        """Icon class for menu."""

    @abc.abstractproperty
    def disp_name(self):
        """Name displayed in menu."""

    def __init__(self, *args, **kwargs):
        super(RalphModule, self).__init__(*args, **kwargs)
        self.register_pattern(
            '',
            r'^{}/'.format(self.url_prefix),
            '{}.urls'.format(self.module_name),
        )
