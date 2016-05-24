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
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import Ethernet, ConfigurationClass
from ralph.data_center.models import DataCenterAsset
from ralph.deployment.models import Preboot
from ralph.dns.views import DNSaaSIntegrationNotEnabledError
from ralph.dns.dnsaas import DNSaaS
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.mixins.forms import ChoiceFieldWithOtherOption, OTHER
from ralph.networks.models import IPAddress, Network, NetworkEnvironment
from ralph.virtual.models import VirtualServer

logger = logging.getLogger(__name__)


NEXT_FREE = _('<NEXT FREE>')
NEXT_FREE_HOSTNAME = 'next_free__network_environment_'
NEXT_FREE_IP = 'next_free__network_'
DEPLOYMENT_MODELS = [DataCenterAsset, VirtualServer]
deployment_action = partial(transition_action, models=DEPLOYMENT_MODELS)


# =============================================================================
# helpers
# =============================================================================


def autocomplete_service_env(actions, objects):
    """
    Returns current service_env for object. Used as a callback for
    `default_value`.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        service_env id
    """
    service_envs = [obj.service_env_id for obj in objects]
    # if service-env for all objects are the same
    if len(set(service_envs)) == 1:
        return service_envs[0]
    return None


def autocomplete_configuration_path(actions, objects):
    """
    Returns current configuration_path for object. Used as a callback for
    `default_value`.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        configuration_path id
    """
    configuration_paths = [obj.configuration_path_id for obj in objects]
    # if configuration paths for all objects are the same
    if len(set(configuration_paths)) == 1:
        return configuration_paths[0]
    return None


def next_free_hostname_choices(actions, objects):
    """
    Generate choices with next free hostname for each network environment
    common for every object.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        list of tuples with next free hostname choices
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
    """
    Generate choices with next free IP for each network common for every object.
    If there is only one object in this transition, custom IP address could be
    passed (OTHER opiton).

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        list of tuples with next free IP choices
    """
    networks = []
    for obj in objects:
        networks.append(set(obj._get_available_networks()))
    networks = set.intersection(*networks)
    ips = [
        (
            '{}{}'.format(NEXT_FREE_IP, network.id),
            '{} ({})'.format(NEXT_FREE, network)
        )
        for network in networks
    ]
    if len(objects) == 1:
        ips += [(OTHER, _('Other'))]
    return ips


def mac_choices_for_objects(actions, objects):
    """
    Generate choices with MAC addresses.

    If there is only object in `objects`, returns list of it's MAC addresses.
    If there is more than one object, return one-elem list with special value
    'use first'.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        list of tuples with MAC addresses
    """
    if len(objects) == 1:
        return [(eth.id, eth.mac) for eth in objects[0].ethernet.filter(
            mac__isnull=False
        )]
    return [('0', _('use first'))]


def _get_non_mgmt_ethernets(instance):
    """
    Returns ethernets of instance which is not used for management IP
    or None if not found.
    """
    return instance.ethernet.filter(
        mac__isnull=False
    ).exclude(
        ipaddress__is_management=True
    ).order_by('mac')


def check_mac_address(instances):
    errors = {}
    for instance in instances:
        if not _get_non_mgmt_ethernets(instance):
            errors[instance] = _('Non-management MAC address not found')
    return errors


# =============================================================================
# transition actions
# =============================================================================
@deployment_action(
    verbose_name=_('Clean hostname'),
)
def clean_hostname(cls, instances, **kwargs):
    for instance in instances:
        logger.warning('Clearing {} hostname ({})'.format(
            instance, instance.hostname
        ))
        instance.hostname = None  # TODO: hostname nullable?


@deployment_action(
    verbose_name=_('Clean DNS entries'),
    run_after=['clean_hostname'],
    is_async=True,
)
def clean_dns(cls, instances, **kwargs):
    if not settings.ENABLE_DNSAAS_INTEGRATION:
        raise DNSaaSIntegrationNotEnabledError()
    dnsaas = DNSaaS()
    # TODO: transaction?
    for instance in instances:
        records = dnsaas.get_dns_records(instance.ipaddresses.all().values_list(
            'address', flat=True
        ))
        for record in records:
            logger.warning(
                'Deleting {pk} ({type} / {name} / {content}) DNS record'.format(
                    **record
                )
            )
            if dnsaas.delete_dns_record(record['pk']):
                raise Exception()  # TODO


@deployment_action(
    verbose_name=_('Clean IP addresses'),
    run_after=['clean_dns'],
)
def clean_ipaddresses(cls, instances, **kwargs):
    for instance in instances:
        for ip in instance.ipaddresses.all():
            # TODO: skip mgmt
            logger.warning('Deleting {} IP address'.format(ip))
            ip.delete()
            # TODO: if there is no mac etc, remove ethernet (overwrite IP delete)


@deployment_action(
    verbose_name=_('Clean DHCP entries'),
    run_after=['clean_dns', 'clean_ipaddresses'],
)
def clean_dhcp(cls, instances, **kwargs):
    for instance in instances:
        mac_addresses = _get_non_mgmt_ethernets(instance).values_list(
            'mac', flat=True
        )
        # TODO when DHCPEntry model will not be proxy to ipaddresse
        # for dhcp_entry in DHCPEntry.objects.filter(mac__in=mac_addresses):
        #     logger.warning('Removing {} DHCP entry')
        #     dhcp_entry.delete()


@deployment_action(
    verbose_name=_('Assign new hostname'),
    form_fields={
        'network_environment': {
            'field': forms.ChoiceField(label=_('Network environment (for hostname)')),
            'choices': next_free_hostname_choices,
            'exclude_from_history': True,  # TODO: history
        },
    },
    run_after=['clean_dns', 'clean_dhcp'],
)
def assign_new_hostname(cls, instances, network_environment, **kwargs):
    net_env_id = network_environment[len(NEXT_FREE_HOSTNAME):]
    net_env = NetworkEnvironment.objects.get(pk=net_env_id)
    for instance in instances:
        new_hostname = net_env.issue_next_free_hostname()
        logger.info('Assigning {} to {}'.format(new_hostname, instance))
        instance.hostname = new_hostname
        instance.save()
        kwargs['history_kwargs'][instance.pk]['hostname'] = (
            '{} (from {})'.format(new_hostname, net_env)
        )


@deployment_action(
    verbose_name=_('Assign new IP address and create DHCP entries'),
    form_fields={
        'ip_or_network': {
            'field': ChoiceFieldWithOtherOption(
                label=_('IP Address'),
                other_field=forms.GenericIPAddressField(),
                auto_other_choice=False,
            ),
            'choices': next_free_ip_choices,
            'exclude_from_history': True,  # TODO: history
            # TODO: validation for IP address (in other field) if not used
        },
        'ethernet': {
            'field': forms.ChoiceField(label=_('MAC Address')),
            'choices': mac_choices_for_objects,
            'exclude_from_history': True,  # TODO: history
        },
    },
    run_after=['assign_new_hostname'],
    precondition=check_mac_address
)
def create_dhcp_entries(cls, instances, ip_or_network, ethernet, **kwargs):
    def _store_history(instance, ip, etherhet):
        kwargs['history_kwargs'][instance.pk].update({
            'ip': ip.address,
            'mac': etherhet.mac,
        })
    if len(instances) == 1:
        ip, ethernet = _create_dhcp_entries_for_single_instance(
            instances[0], ip_or_network, ethernet
        )
        _store_history(instances[0], ip, ethernet)
    else:
        for instance, (ip, ethernet) in zip(
            _create_dhcp_entries_for_many_instances(
                instances, ip_or_network
            ),
            instances
        ):
            _store_history(instance, ip, ethernet)


def _create_dhcp_entries_for_single_instance(instance, ip_or_network, ethernet_id):
    if ip_or_network['value'] == OTHER:
        ip_address = ip_or_network[OTHER]
        ip = IPAddress.objects.create(address=ip_address)
    else:
        network = Network.objects.get(
            pk=ip_or_network['value'][len(NEXT_FREE_IP):]
        )
        ip = network.issue_next_free_ip()
    ethernet = Ethernet.objects.get(pk=ethernet_id)
    ip.ethernet = ethernet
    ip.save()
    # TODO when DHCPEntry model will not be proxy to IPAddress
    # DHCPEntry.objects.create(mac=ethernet.mac, ip=ip.address)
    return ip, ethernet


def _create_dhcp_entries_for_many_instances(instances, ip_or_network):
    for instance in instances:
        # when IP is assigned to many instances, mac is not provided through
        # form and first non-mgmt mac should be used
        ethernet = _get_non_mgmt_ethernets(instance).values_list(
            'id', flat=True
        ).first()
        yield _create_dhcp_entries_for_single_instance(
            instance, ip_or_network, ethernet
        )


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
        instance.save()


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
        logger.info('Assinging {} configuration path to {}'.format(
            ConfigurationClass.objects.get(pk=configuration_path),
            instance
        ))
        instance.configuration_path_id = configuration_path
        instance.save()


@deployment_action(
    verbose_name=_('Apply preboot'),
    form_fields={
        'preboot': {
            'field': forms.ModelChoiceField(
                label=_('Preboot'),
                queryset=Preboot.objects.all(),
                empty_label=None
            ),
        }
    },
    is_async=True,
    run_after=['assign_new_hostname', 'create_dhcp_entries'],
)
def deploy(cls, instances, **kwargs):
    """
    This function just indicates that it's deployment transition.
    """
    pass


@deployment_action(
    verbose_name=_('Wait for ping'),
    is_async=True,
    run_after=['deploy'],
)
def wait_for_ping(cls, instances, **kwargs):
    pass  # TODO
