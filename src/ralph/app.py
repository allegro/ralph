"""Ralph extension for DjangoPluggableApp."""

import abc
import pluggableapp
from pkg_resources import iter_entry_points


class RalphModule(pluggableapp.PluggableApp):

    """A pluggable application that depends on ralph and is accessible from
    the ralph main application."""

    metaclass = abc.ABCMeta
    required_permission = None

    @classmethod
    def api_resources(self, version):
        """Returns a list of API resources to be mounted for a given version
        of API."""
        return []

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


def mount_api(api):
    """Searches the pluggable apps for resources to be mounted on API
    with a given version and adds them to a given API object."""

    for entry_point in iter_entry_points('django.pluggable_app'):
        app = entry_point.load()
        if isinstance(app, type) and issubclass(app, RalphModule):
            for resource in app.api_resources(api):
                api.register(resource)
