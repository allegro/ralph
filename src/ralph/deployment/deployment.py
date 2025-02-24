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

import ipaddress
import logging
import time
from datetime import datetime
from functools import partial

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import ConfigurationClass, Ethernet
from ralph.data_center.models import DataCenterAsset
from ralph.deployment.models import Preboot
from ralph.dhcp.models import DHCPEntry, DHCPServer
from ralph.dns.dnsaas import DNSaaS
from ralph.dns.forms import RecordType
from ralph.dns.views import DNSaaSIntegrationNotEnabledError
from ralph.lib.mixins.forms import ChoiceFieldWithOtherOption, OTHER
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.exceptions import FreezeAsyncTransition
from ralph.networks.models import IPAddress, Network, NetworkEnvironment
from ralph.virtual.models import VirtualServer

logger = logging.getLogger(__name__)


NEXT_FREE = _("<NEXT FREE>")
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
        network_environments.append(set(obj._get_available_network_environments()))
    # get common part
    network_environments = set.intersection(*network_environments)
    hostnames = [
        (str(net_env.id), "{} ({})".format(net_env.next_free_hostname, net_env))
        for net_env in network_environments
    ]
    if len(objects) == 1:
        hostnames += [(OTHER, _("Other"))]
    return hostnames


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
        networks.append(set(obj._get_available_networks(is_broadcasted_in_dhcp=True)))
    # get common part
    networks = set.intersection(*networks)
    ips = [
        (str(network.id), "{} ({})".format(network.get_first_free_ip(), network))
        for network in networks
    ]
    return ips


def next_free_ip_choices_wth_other_choice(actions, objects):
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
    ips = next_free_ip_choices(actions, objects)
    # if there is only one object, allow for Other option typed by user
    if len(objects) == 1:
        ips += [(OTHER, _("Other"))]
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
        return [
            (eth.id, eth.mac)
            for eth in objects[0].ethernet_set.filter(
                Q(ipaddress__is_management=False) | Q(ipaddress__isnull=True),
                mac__isnull=False,
            )
        ]
    # TODO: when some object has more than one Ethernets (non-mgmt), should
    # raise exception?
    return [("0", _("use first"))]


def dhcp_entries_for_objects(actions, objects):
    """
    Generate choices with DHCP entries.

    If there is only object in `objects`, returns list of it's MAC addresses.
    Runnig this action for more than one object at a time is not allowed.

    Args:
        actions: Transition action list
        objects: Django models objects

    Returns:
        list of tuples with DHCP entries.
    """
    if len(objects) == 1:
        return [
            (
                ip.id,
                "{} ({}) / {}".format(
                    ip.address,
                    ip.hostname,
                    # theoritically should never happen...
                    ip.ethernet.mac if ip.ethernet else None,
                ),
            )
            for ip in objects[0].ipaddresses.filter(dhcp_expose=True)
        ]
    # TODO: don't allow to run this action when more than one object selected
    return []


def _get_non_mgmt_ethernets(instance):
    """
    Returns ethernets of instance which is not used for management IP.

    Args:
        instance: BaseObject instance
    """
    return (
        instance.ethernet_set.filter(mac__isnull=False)
        .exclude(ipaddress__is_management=True)
        .order_by("mac")
    )


def check_if_deployment_is_available(instances, **kwargs):
    """
    Check if deployment is available.
    """
    errors = {}
    for instance in instances:
        if (
            isinstance(instance, DataCenterAsset)
            and not instance.model.category.allow_deployment
        ):
            errors[instance] = _(
                (
                    "Deployment is not available for this asset"
                    " with category: %(category)s."
                )
                % {"category": instance.model.category.name}
            )
    return errors


def check_mac_address(instances, **kwargs):
    """
    Verify, that each instance has at least one non-management MAC.
    """
    errors = {}
    for instance in instances:
        if not _get_non_mgmt_ethernets(instance):
            errors[instance] = _("Non-management MAC address not found")
    return errors


def check_if_network_environment_exists(instances, **kwargs):
    """
    Verify, that each instance has network environment exists.
    """
    errors = {}
    for instance in instances:
        if not instance._get_available_network_environments():
            errors[instance] = _("Network environment not found.")
    return errors


# =============================================================================
# transition actions
# =============================================================================
@deployment_action(
    verbose_name=_("Clean hostname"),
)
def clean_hostname(cls, instances, **kwargs):
    """
    Clear hostname for each instance
    """
    for instance in instances:
        logger.warning("Clearing %s hostname (%s)", instance, instance.hostname)
        instance.hostname = None  # TODO: hostname nullable?


@deployment_action(
    verbose_name=_("Clean DNS entries"),
    run_after=["clean_hostname"],
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
        ips = list(
            instance.ipaddresses.exclude(is_management=True).values_list(
                "address", flat=True
            )
        )
        if not ips:
            logger.info("No IPs for %s - skipping cleaning DNS entries", instance)
            continue
        records = dnsaas.get_dns_records(ips)
        if len(records) > settings.DEPLOYMENT_MAX_DNS_ENTRIES_TO_CLEAN:
            raise Exception(
                "Cannot clean {} entries for {} - clean it manually".format(
                    len(records), instance
                )
            )
        for record in records:
            logger.warning(
                "Deleting %s (%s / %s / %s) DNS record",
                record["pk"],
                record["type"],
                record["name"],
                record["content"],
            )
            if dnsaas.delete_dns_record(record["pk"]):
                raise Exception()  # TODO


@deployment_action(
    verbose_name=_("Clean IP addresses"),
    run_after=["clean_dns"],
)
def clean_ipaddresses(cls, instances, **kwargs):
    """
    Clean IP addresses (non-management) for each instance.
    """
    for instance in instances:
        for ip in instance.ipaddresses.exclude(is_management=True):
            logger.warning("Deleting %s IP address", ip)
            eth = ip.ethernet
            ip.delete()
            if not any([eth.mac, eth.label]):
                logger.warning("Deleting %s (%s) ethernet", eth, eth.id)
                eth.delete()


@deployment_action(
    verbose_name=_("Clean DHCP entries"),
    run_after=["clean_dns", "clean_ipaddresses"],
)
def clean_dhcp(cls, instances, **kwargs):
    """
    Clean DHCP entries for each instance.
    """
    for instance in instances:
        _get_non_mgmt_ethernets(instance).values_list("mac", flat=True)
        for dhcp_entry in DHCPEntry.objects.filter(
            ethernet__base_object=instance, dhcp_expose=True
        ):
            logger.warning("Removing %s DHCP entry", dhcp_entry)
            dhcp_entry.delete()


@deployment_action(
    verbose_name=_("Remove from DHCP entries"),
    form_fields={
        "ipaddress": {
            "field": forms.ChoiceField(label=_("DHCP Entry")),
            "choices": dhcp_entries_for_objects,
            "exclude_from_history": True,
        },
    },
)
def remove_from_dhcp_entries(cls, instances, ipaddress, **kwargs):
    """
    Clean DHCP entries for each instance.
    """
    ip = IPAddress.objects.get(pk=ipaddress)
    entry = "{} ({}) / {}".format(
        ip.address, ip.hostname, ip.ethernet.mac if ip.ethernet else None
    )
    logger.warning("Removing entry from DHCP: %s", entry)
    kwargs["history_kwargs"][instances[0].pk]["DHCP entry"] = entry
    ip.dhcp_expose = False
    ip.save()


@deployment_action(
    verbose_name=_("Assign new hostname"),
    form_fields={
        "network_environment": {
            "field": ChoiceFieldWithOtherOption(
                label=_("Hostname"),
                other_field=forms.CharField(),
                auto_other_choice=False,
            ),
            "choices": next_free_hostname_choices,
            "exclude_from_history": True,
        },
    },
    run_after=["clean_dns", "clean_dhcp", "clean_hostname"],
)
def assign_new_hostname(cls, instances, network_environment, **kwargs):
    """
    Assign new hostname for each instance based on selected network environment.
    """

    def _assign_hostname(instance, new_hostname, net_env=None):
        logger.info("Assigning {} to {}".format(new_hostname, instance))
        instance.hostname = new_hostname
        instance.save()
        kwargs["history_kwargs"][instance.pk]["hostname"] = "{}{}".format(
            new_hostname, " (from {})".format(net_env) if net_env else ""
        )
        kwargs["shared_params"]["hostnames"][instance.pk] = new_hostname

    if "hostnames" not in kwargs["shared_params"]:
        kwargs["shared_params"]["hostnames"] = {}

    if network_environment["value"] == OTHER:
        hostname = network_environment[OTHER]
        # when OTHER value posted, there could be only one instance
        _assign_hostname(instances[0], hostname)
    else:
        net_env = NetworkEnvironment.objects.get(pk=network_environment["value"])
        for instance in instances:
            new_hostname = net_env.issue_next_free_hostname()
            _assign_hostname(instance, new_hostname, net_env)


def validate_ip_address(instances, data):
    if data["ip_or_network"]["value"] == OTHER:
        assert len(instances) == 1
        instance = instances[0]
        address = data["ip_or_network"][OTHER]
        check_ip_from_defined_network(address)
        check_ipaddress_unique(instance, address)


def check_ipaddress_unique(instance, address):
    """
    Validate if `address` is already assigned to another (base) object.
    """
    try:
        ip = IPAddress.objects.get(address=address)
    except IPAddress.DoesNotExist:
        pass
    else:
        if ip.ethernet and ip.ethernet.base_object_id != instance.pk:
            raise ValidationError(
                "IP {} is already assigned to other object!".format(address)
            )


def check_ip_from_defined_network(address):
    """
    Validate if `address` belongs to any network already added
    """
    ip = ipaddress.ip_address(address)
    if not Network.objects.filter(min_ip__lte=int(ip), max_ip__gte=int(ip)):
        raise ValidationError("IP {} doesn't belong to any network!".format(address))


@deployment_action(
    verbose_name=_("Assign new IP"),
    form_fields={
        "network": {
            "field": forms.ChoiceField(label=_("IP Address")),
            "choices": next_free_ip_choices,
            "exclude_from_history": True,
        },
    },
    run_after=["assign_new_hostname"],
)
def assign_new_ip(cls, instances, network, **kwargs):
    for instance in instances:
        network = Network.objects.get(pk=network)
        ip = network.issue_next_free_ip()
        logger.info("Assigning {} to {}".format(ip, instance))
        ethernet = Ethernet.objects.create(base_object=instance)
        logger.info("Bounding {} to {} ethernet".format(ip, ethernet))
        ip.ethernet = ethernet

        try:
            hostname = kwargs["shared_params"]["hostnames"].get(instance.pk)
            if hostname:
                ip.hostname = hostname
        except KeyError:
            pass

        ip.save()


def base_object_ip_choices(actions, objects):
    ipaddresses = []
    for instance in objects:
        for ip in instance.ipaddresses:
            ipaddresses.append([ip.id, "{} - {}".format(ip.address, ip.hostname)])
    return ipaddresses


def base_object_network_choices(actions, objects):
    networks = []
    for instance in objects:
        for network in instance._get_available_networks():
            networks.append([network.id, network])
    return networks


def check_number_of_instance(instances, **kwargs):
    """
    Verify, if number of asset is equal to 1.

    Args:
        instances: Django model object instances
    Returns:
        errors: Dict
    """
    errors = {}
    if len(instances) > 1:
        errors[instances[0]] = _("You can choose only one asset")

    return errors


@deployment_action(
    verbose_name=_("Replace IP"),
    form_fields={
        "ipaddress": {
            "field": forms.ChoiceField(
                label=_("IP Address"),
            ),
            "choices": base_object_ip_choices,
            "exclude_from_history": True,
        },
        "network": {
            "field": forms.ChoiceField(
                label=_("Network"),
            ),
            "choices": base_object_network_choices,
            "exclude_from_history": True,
        },
    },
    precondition=check_number_of_instance,
)
def replace_ip(cls, instances, ipaddress, network, **kwargs):
    ip = IPAddress.objects.get(pk=ipaddress)
    network = Network.objects.get(pk=network)
    new_ip_address = str(network.get_first_free_ip())
    logger.info("Replacing IP {} to {}".format(ip.address, new_ip_address))
    ip.address = new_ip_address
    ip.save()


@deployment_action(
    verbose_name=_("Assign new IP address and create DHCP entries"),
    form_fields={
        "ip_or_network": {
            "field": ChoiceFieldWithOtherOption(
                label=_("IP Address"),
                other_field=forms.GenericIPAddressField(),
                auto_other_choice=False,
            ),
            "choices": next_free_ip_choices_wth_other_choice,
            "exclude_from_history": True,
            "validation": validate_ip_address,
        },
        "ethernet": {
            "field": forms.ChoiceField(label=_("MAC Address")),
            "choices": mac_choices_for_objects,
            "exclude_from_history": True,  # TODO: history
        },
    },
    run_after=["assign_new_hostname", "clean_ipaddresses", "clean_dhcp"],
    precondition=check_mac_address,
)
def create_dhcp_entries(cls, instances, ip_or_network, ethernet, **kwargs):
    """
    Assign next free IP to each instance and create DHCP entries for it.
    """

    def _store_history(instance, ip, etherhet):
        kwargs["history_kwargs"][instance.pk].update(
            {
                "ip": ip.address,
                "mac": etherhet.mac,
            }
        )

    if len(instances) == 1:
        ip, ethernet = _create_dhcp_entries_for_single_instance(
            instances[0], ip_or_network, ethernet
        )
        _store_history(instances[0], ip, ethernet)
        kwargs["shared_params"]["ip_addresses"][instances[0].pk] = ip
    else:
        for instance, (ip, ethernet) in zip(
            _create_dhcp_entries_for_many_instances(instances, ip_or_network), instances
        ):
            _store_history(instance, ip, ethernet)
            kwargs["shared_params"]["ip_addresses"][instance.pk] = ip

    kwargs["shared_params"]["dhcp_entry_created_date"] = datetime.now()


def _create_dhcp_entries_for_single_instance(instance, ip_or_network, ethernet_id):
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
    if ip_or_network["value"] == OTHER:
        ip_address = ip_or_network[OTHER]
        ip = IPAddress.objects.create(address=ip_address)
    else:
        network = Network.objects.get(pk=ip_or_network["value"])
        ip = network.issue_next_free_ip()
    logger.info("Assigning {} to {}".format(ip, instance))
    # pass base_object as param to make sure that this ethernet is assigned
    # to currently transitioned instance
    ethernet = Ethernet.objects.get(pk=ethernet_id, base_object=instance)
    ip.hostname = instance.hostname
    logger.info("Bounding {} to {} ethernet".format(ip, ethernet))
    ip.ethernet = ethernet
    ip.dhcp_expose = True
    ip.save()
    return ip, ethernet


def _create_dhcp_entries_for_many_instances(instances, ip_or_network):
    """
    Assign IP and create DHCP entries for multiple instances.
    """
    for instance in instances:
        # when IP is assigned to many instances, mac is not provided through
        # form and first non-mgmt mac should be used
        ethernet = (
            _get_non_mgmt_ethernets(instance).values_list("id", flat=True).first()
        )  # TODO: is first the best choice here?
        yield _create_dhcp_entries_for_single_instance(
            instance, ip_or_network, ethernet
        )


@deployment_action(
    verbose_name=_("Wait for DHCP servers"),
    is_async=True,
    run_after=["create_dhcp_entries"],
    precondition=check_if_network_environment_exists,
)
def wait_for_dhcp_servers(cls, instances, **kwargs):
    """
    Wait until DHCP servers ping to Ralph.
    """
    created = kwargs["shared_params"]["dhcp_entry_created_date"]
    # TODO: rescheduler instead of while
    network_environment_ids = []
    for ip in kwargs["shared_params"]["ip_addresses"].values():
        network_environment_ids.append(ip.network.network_environment_id)

    while True:
        servers_sync_list = DHCPServer.objects.filter(
            Q(network_environment__isnull=True)
            | Q(network_environment_id__in=network_environment_ids)
        ).values_list("last_synchronized", flat=True)
        for server_sync_date in servers_sync_list:
            if created < server_sync_date:
                return
        time.sleep(1)


@deployment_action(
    verbose_name=_("Create DNS entries"),
    run_after=["assign_new_hostname", "create_dhcp_entries"],
)
def create_dns_entries(cls, instances, **kwargs):
    if not settings.ENABLE_DNSAAS_INTEGRATION:
        raise DNSaaSIntegrationNotEnabledError()
    dnsaas = DNSaaS()
    # TODO: transaction?
    for instance in instances:
        # TODO: use dedicated param instead of history_kwargs
        ip = kwargs["history_kwargs"][instance.pk]["ip"]
        dnsaas.create_dns_record(
            record={
                "name": instance.hostname,
                "type": RecordType.a.id,
                "content": ip,
                "ptr": True,
            },
            service=instance.service,
        )


@deployment_action(
    verbose_name=_("Change service-env"),
    form_fields={
        "service_env": {
            "field": forms.CharField(label=_("Service-environment")),
            "autocomplete_field": "service_env",
            "default_value": autocomplete_service_env,
        },
    },
    run_after=["clean_dns", "clean_dhcp"],
)
def assign_service_env(cls, instances, service_env, **kwargs):
    """
    Assign service-env to each instance.
    """
    for instance in instances:
        instance.service_env_id = service_env
        instance.save()


@deployment_action(
    verbose_name=_("Change configuration_path"),
    form_fields={
        "configuration_path": {
            "field": forms.CharField(label=_("Configuration path")),
            "autocomplete_field": "configuration_path",
            "default_value": autocomplete_configuration_path,
        },
    },
    run_after=["clean_dns", "clean_dhcp"],
)
def assign_configuration_path(cls, instances, configuration_path, **kwargs):
    """
    Assign configuration path to each instance.
    """
    for instance in instances:
        logger.info(
            "Assinging {} configuration path to {}".format(
                ConfigurationClass.objects.get(pk=configuration_path), instance
            )
        )
        instance.configuration_path_id = configuration_path
        instance.save()


def get_preboot_choices(actions, objects):
    choices = []
    for obj in Preboot.active_objects.order_by(
        "name",
    ):
        if obj.critical_after and obj.critical_after < timezone.now().date():
            label = f"[CRITICAL!]{obj.name}"
        elif obj.warning_after and obj.warning_after < timezone.now().date():
            label = f"[WARNING!]{obj.name}"
        else:
            label = obj.name
        choices.append((obj.id, label))
    return choices


@deployment_action(
    verbose_name=_("Apply preboot"),
    form_fields={
        "preboot": {
            "field": forms.ChoiceField(
                label=_("Preboot"), widget=forms.Select(attrs={"id": "preboot-select"})
            ),
            "choices": get_preboot_choices,
        }
    },
    is_async=True,
    run_after=[
        "assign_new_hostname",
        "create_dhcp_entries",
        "wait_for_dhcp_servers",
        "create_dns_entries",
    ],
    precondition=check_if_deployment_is_available,
)
def deploy(cls, instances, **kwargs):
    """
    This function just indicates that it's deployment transition.
    """
    # freeze transition and wait for "ping" from server
    raise FreezeAsyncTransition()


@deployment_action(
    verbose_name=_("Wait for ping"),
    is_async=True,
    run_after=["deploy"],
)
def wait_for_ping(cls, instances, tja, **kwargs):
    """
    Wait until server ping to Ralph that is has properly deployed.
    """
    pass
