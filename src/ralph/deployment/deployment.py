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

"""
import logging
import time
from datetime import datetime
from functools import partial

from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import ConfigurationClass, Ethernet
from ralph.data_center.models import DataCenterAsset
from ralph.deployment.models import Preboot
from ralph.dhcp.models import DHCPServer
from ralph.dns.dnsaas import DNSaaS
from ralph.dns.forms import RecordType
from ralph.dns.views import DNSaaSIntegrationNotEnabledError
from ralph.lib.mixins.forms import ChoiceFieldWithOtherOption, OTHER
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.models import TransitionJobActionStatus
from ralph.networks.models import IPAddress, Network, NetworkEnvironment
from ralph.virtual.models import VirtualServer

logger = logging.getLogger(__name__)


NEXT_FREE = _('<NEXT FREE>')
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
    # get common part
    network_environments = set.intersection(*network_environments)
    return [
        (
            str(net_env.id),
            '{} ({})'.format(net_env.next_free_hostname, net_env)
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
    # get common part
    networks = set.intersection(*networks)
    ips = [
        (
            str(network.id),
            '{} ({})'.format(network.get_first_free_ip(), network)
        )
        for network in networks
    ]
    # if there is only one object, allow for Other option typed by user
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
            Q(ipaddress__is_management=False) | Q(ipaddress__isnull=True),
            mac__isnull=False,
        )]
    # TODO: when some object has more than one Ethernets (non-mgmt), should
    # raise exception?
    return [('0', _('use first'))]


def _get_non_mgmt_ethernets(instance):
    """
    Returns ethernets of instance which is not used for management IP.

    Args:
        instance: BaseObject instance
    """
    return instance.ethernet.filter(
        mac__isnull=False
    ).exclude(
        ipaddress__is_management=True
    ).order_by('mac')


def check_mac_address(instances):
    """
    Verify, that each instance has at least one non-management MAC.
    """
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
    """
    Clear hostname for each instance
    """
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
    """
    Clean DNS entries for each instance if DNSaaS integration is enabled.
    """
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
    """
    Clean IP addresses (non-management) for each instance.
    """
    for instance in instances:
        for ip in instance.ipaddresses.exclude(is_management=True):
            logger.warning('Deleting {} IP address'.format(ip))
            eth = ip.ethernet
            ip.delete()
            if not any([eth.mac, eth.label]):
                logger.warning('Deleting {} ({}) ethernet'.format(eth, eth.id))
                eth.delete()


@deployment_action(
    verbose_name=_('Clean DHCP entries'),
    run_after=['clean_dns', 'clean_ipaddresses'],
)
def clean_dhcp(cls, instances, **kwargs):
    """
    Clean DHCP entries for each instance.
    """
    for instance in instances:
        _get_non_mgmt_ethernets(instance).values_list('mac', flat=True)
        # TODO when DHCPEntry model will not be proxy to ipaddresse
        # for dhcp_entry in DHCPEntry.objects.filter(mac__in=mac_addresses):
        #     logger.warning('Removing {} DHCP entry')
        #     dhcp_entry.delete()


@deployment_action(
    verbose_name=_('Assign new hostname'),
    form_fields={
        'network_environment': {
            'field': forms.ChoiceField(
                label=_('Network environment (for hostname)')
            ),
            'choices': next_free_hostname_choices,
            'exclude_from_history': True,
        },
    },
    run_after=['clean_dns', 'clean_dhcp'],
)
def assign_new_hostname(cls, instances, network_environment, **kwargs):
    """
    Assign new hostname for each instance based on selected network environment.
    """
    net_env = NetworkEnvironment.objects.get(pk=network_environment)
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
            'exclude_from_history': True,
            # TODO: validation for IP address (in other field) if not used
            # by other object
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
    """
    Assign next free IP to each instance and create DHCP entries for it.
    """
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
    # TODO: use dedicated key
    kwargs['history_kwargs']['dhcp_entry_created_date'] = datetime.now()


def _create_dhcp_entries_for_single_instance(
    instance, ip_or_network, ethernet_id
):
    """
    Assign IP and create DHCP entries for single instance.

    Args:
        instance: BaseObject instance
        ip_or_network: value from ChoiceFieldWithOtherOption (network or custom
            IP address)
        ethernet_id: id of Ethernet component.

    Returns:
        tuple with (new IP, ethernet component)
    """
    if ip_or_network['value'] == OTHER:
        ip_address = ip_or_network[OTHER]
        ip = IPAddress.objects.create(address=ip_address)
    else:
        network = Network.objects.get(
            pk=ip_or_network['value']
        )
        ip = network.issue_next_free_ip()
    ethernet = Ethernet.objects.get(pk=ethernet_id)
    ip.hostname = instance.hostname
    ip.ethernet = ethernet
    ip.save()
    # TODO when DHCPEntry model will not be proxy to IPAddress
    # DHCPEntry.objects.create(mac=ethernet.mac, ip=ip.address)
    return ip, ethernet


def _create_dhcp_entries_for_many_instances(instances, ip_or_network):
    """
    Assign IP and create DHCP entries for multiple instances.
    """
    for instance in instances:
        # when IP is assigned to many instances, mac is not provided through
        # form and first non-mgmt mac should be used
        ethernet = _get_non_mgmt_ethernets(instance).values_list(
            'id', flat=True
        ).first()  # TODO: is first the best choice here?
        yield _create_dhcp_entries_for_single_instance(
            instance, ip_or_network, ethernet
        )


@deployment_action(
    verbose_name=_('Wait for DHCP servers'),
    is_async=True,
    run_after=['create_dhcp_entries'],
)
def wait_for_dhcp_servers(cls, instances, **kwargs):
    """
    Wait until DHCP servers ping to Ralph.
    """
    created = kwargs['history_kwargs']['dhcp_entry_created_date']
    # TODO: rescheduler instead of while
    while True:
        servers_sync_date = DHCPServer.objects.values_list(
            'last_synchronized', flat=True
        ).all()
        for server_sync_date in servers_sync_date:
            if created < server_sync_date:
                return
        time.sleep(1)


@deployment_action(
    verbose_name=_('Create DNS entries'),
    run_after=[
        'assign_new_hostname', 'create_dhcp_entries'
    ],
)
def create_dns_entries(cls, instances, **kwargs):
    if not settings.ENABLE_DNSAAS_INTEGRATION:
        raise DNSaaSIntegrationNotEnabledError()
    dnsaas = DNSaaS()
    # TODO: transaction?
    for instance in instances:
        # TODO: use dedicated param instead of history_kwargs
        ip = kwargs['history_kwargs'][instance.pk]['ip']
        dnsaas.create_dns_record({
            'name': instance.hostname,
            'type': RecordType.a.id,
            'content': ip,
        })


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
    """
    Assign service-env to each instance.
    """
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
    """
    Assign configuration path to each instance.
    """
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
def wait_for_ping(cls, instances, tja, **kwargs):
    """
    Wait until server ping to Ralph that is has properly deployed.
    """
    while tja.status == TransitionJobActionStatus.STARTED:
        tja.refresh_from_db()
        time.sleep(1)
