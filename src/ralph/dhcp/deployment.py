# -*- coding: utf-8 -*-
"""
Transition actions for deployment

Deployment order:
* cleaning
    * clean hostname
    * clean IP addresses
    * clean DNS entries
    * clean DHCP entries
    * clean ???
* Generate and assign new hostname
* Generete (or use passed) and assign IP address
* Assign (new) service-env
* Assign (new) configuration_path
* Make DNS records
* Make DHCP entries
* Wait for ping
* Reboot ?

"""
import logging
from functools import partial

from django import forms
from django.utils.translation import ugettext_lazy as _

from ralph.virtual.models import VirtualServer
from ralph.data_center.models import DataCenterAsset
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.mixins.forms import ChoiceFieldWithOtherOption

logger = logging.getLogger(__name__)


NEXT_FREE = _('<NEXT FREE>')
NEXT_FREE_HOSTNAME = 'next_free__network_environment_'
NEXT_FREE_IP = 'next_free__network_'
DEPLOYMENT_MODELS = [DataCenterAsset, VirtualServer]
deployment_action = partial(transition_action, models=DEPLOYMENT_MODELS)


def autocomplete_service_env(actions, objects):
    """Function used as a callback for default_value.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        int object's pk
    """
    service_envs = [obj.service_env_id for obj in objects]
    # if service-env for all objects are the same
    if len(set(service_envs)) == 1:
        return service_envs[0]
    return False  # TODO: improve


def autocomplete_configuration_path(actions, objects):
    """Function used as a callback for default_value.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        int object's pk
    """
    configuration_paths = [obj.configuration_path_id for obj in objects]
    # if configuration paths for all objects are the same
    if len(set(configuration_paths)) == 1:
        return configuration_paths[0]
    return False  # TODO: improve


def next_free_hostname_choices(actions, objects):
    """Function used as a callback for default_value.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        string next free hostname based on network environment
    """
    network_environments = []
    for obj in objects:
        network_environments.append(
            set(obj._get_available_network_environments())
        )
    network_environments = set.intersection(*network_environments)
    return [
        (
            '{}{}'.format(NEXT_FREE_HOSTNAME, net_env.id),
            '{} ({})'.format(NEXT_FREE, net_env)
        )
        for net_env in network_environments
    ]


def next_free_ip_choices(actions, objects):
    networks = []
    for obj in objects:
        networks.append(set(obj._get_available_networks()))
    networks = set.intersection(*networks)
    return [
        (
            '{}{}'.format(NEXT_FREE_IP, network.id),
            '{} ({})'.format(NEXT_FREE, network)
        )
        for network in networks
    ]


def mac_choices_for_objects(actions, objects):
    """Function used as a callback for choices.
    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        list tuple pairs (value, label)
    """
    if len(objects) == 1:
        return [(eth.id, eth.mac) for eth in objects[0].ethernet.all()]
    return [('0', _('use first'))]


@deployment_action(
    verbose_name=_('Clean hostname'),
)
def clean_hostname(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Clean DNS entries'),
    run_after=['clean_hostname'],
    is_async=True,
)
def clean_dns(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Clean IP addresses'),
    run_after=['clean_dns'],
)
def clean_ipaddresses(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Clean DHCP entries'),
    run_after=['clean_dns', 'clean_ipaddresses'],
)
def clean_dhcp(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Assign new hostname'),
    disable_save_object=True,
    form_fields={
        'hostname': {
            'field': forms.ChoiceField(label=_('Hostname')),
            'choices': next_free_hostname_choices
        },
    },
    run_after=['clean_dns', 'clean_dhcp'],
)
def assign_new_hostname(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Assign new IP address'),
    disable_save_object=True,
    form_fields={
        'ip_or_network': {
            'field': ChoiceFieldWithOtherOption(
                label=_('IP Address'),
                other_field=forms.GenericIPAddressField(),
            ),
            'choices': next_free_ip_choices
        },
    },
)
def assign_ip(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Change service-env'),
    form_fields={
        'service_env': {
            'field': forms.CharField(label=_('Service-environment')),
            'autocomplete_field': 'service_env',
            'default_value': autocomplete_service_env
        },
    },
    run_after=['clean_dns', 'clean_dhcp'],
)
def assign_service_env(cls, instances, service_env, **kwargs):
    for instance in instances:
        instance.service_env_id = service_env


@deployment_action(
    verbose_name=_('Change configuration_path'),
    form_fields={
        'configuration_path': {
            'field': forms.CharField(label=_('Configuration path')),
            'autocomplete_field': 'configuration_path',
            'default_value': autocomplete_configuration_path
        },
    },
    run_after=['clean_dns', 'clean_dhcp'],
)
def assign_configuration_path(cls, instances, configuration_path, **kwargs):
    for instance in instances:
        instance.configuration_path_id = configuration_path


@deployment_action(
    verbose_name=_('Create DHCP entries'),
    disable_save_object=True,
    form_fields={
        'mac': {
            'field': forms.ChoiceField(label=_('MAC Address')),
            'choices': mac_choices_for_objects
        },
        # TODO: deployment models
        'preboot': {
            'field': forms.ChoiceField(label=_('Preboot')),
            'choices': [
                (1, 'Ubuntu 14.04'),
                (2, 'Ubuntu 14.10'),
                (3, 'Ubuntu 15.04'),
            ],
        }
    }
)
def create_dhcp_entries(cls, instances, **kwargs):
    pass  # TODO


@deployment_action(
    verbose_name=_('Wait for ping'),
    disable_save_object=True,
    is_async=True,
)
def wait_for_ping(cls, instances, **kwargs):
    pass  # TODO
