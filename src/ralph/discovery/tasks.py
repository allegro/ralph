#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Asynchronous task support for discovery."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, timedelta
from functools import partial
import random
import re
import textwrap
import traceback

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import django_rq
from ipaddr import IPv4Network, IPv6Network

from ralph.discovery.models import Network, IPAddress
from ralph.util.network import ping
from ralph.util import output, plugin


DNS_TXT_ATTRIBUTE_REGEX = re.compile(r'(?P<attribute>[^:]+): (?P<value>.*)')
MAX_RESTARTS = 3
SANITY_CHECK_PING_ADDRESS = settings.SANITY_CHECK_PING_ADDRESS
SINGLE_DISCOVERY_TIMEOUT = settings.SINGLE_DISCOVERY_TIMEOUT


class Error(Exception):

    """Errors during discovery tasks."""


class NoQueueError(Error):

    """No discovery queue defined."""


def set_queue(context):
    """Route the discovery tasks to the right data center for them.
    Use the default queue if no network matches the IP address.
    """
    try:
        queue = context['queue']
    except KeyError:
        queue = 'default'
        try:
            net = Network.from_ip(context['ip'])
        except KeyError:
            pass
        else:
            if net.environment and net.environment.queue:
                queue = net.environment.queue.name
        context['queue'] = queue


def sanity_check(perform_network_checks=True):
    """Checks configuration integrity by pinging the SANITY_CHECK_PING_ADDRESS.
    """
    if not perform_network_checks:
        return

    if ping(SANITY_CHECK_PING_ADDRESS) is None:
        raise ImproperlyConfigured(
            textwrap.dedent(
                """
                fatal: {} is not pingable.

                Things you might want to check:
                * is this host connected to network
                * is this domain pingable from your terminal
                * is your python binary capped with setcap CAP_NET_RAW
                or
                * are you running tests from root
                or
                * are you using setuid bin/python
                """
            ).strip().format(SANITY_CHECK_PING_ADDRESS),
        )


def dummy_task(interactive=False, index=None):
    stdout = output.get(interactive)
    if index:
        if not index % 25:
            raise LookupError(
                "You called {} and it failed on purpose.".format(index),
            )
        stdout("Ping {}.".format(index))
    else:
        stdout("Ping.")


def dummy_horde(interactive=False, how_many=1000):
    if interactive:
        for i in xrange(how_many):
            dummy_task(interactive=interactive, index=i + 1)
    else:
        queue = django_rq.get_queue()
        for i in xrange(how_many):
            queue.enqueue_call(
                func=dummy_task,
                kwargs=dict(interactive=interactive, index=i + 1),
                timeout=60,
                result_ttl=0,
            )


def run_next_plugin(context, chains, requirements=None, interactive=False,
                    done_requirements=None, outputs=None, after=None):
    """Runs the next plugin, asynchronously if interactive=False is given."""

    if requirements is None:
        requirements = set()
    if done_requirements is None:
        done_requirements = set()
    run = _select_run_method(context, interactive, run_plugin, after)
    for index, chain in enumerate(chains):
        to_run = plugin.next(chain, requirements) - done_requirements
        if to_run:
            plugin_name = plugin.highest_priority(chain, to_run)
            run(context, chains[index:], plugin_name, requirements,
                interactive, done_requirements, outputs)
            return


def run_chain(context, chain_name, requirements=None, interactive=False,
              done_requirements=None, outputs=None,
              after=None):
    """Runs a single chain in its entirety at once, asynchronously if
    interactive=False is given.
    """

    run = _select_run_method(context, interactive, _run_chain, after)
    run(context, chain_name, requirements, interactive, done_requirements,
        outputs)


def run_plugin(context, chains, plugin_name,
               requirements=None, interactive=False, done_requirements=None,
               restarts=MAX_RESTARTS, outputs=None):
    """Synchronously runs a plugin named `plugin_name` from the first of the
    specified `chains` using a given `context`. Automatically advances the
    chain scheduling the next plugin to be run. When no plugins are left in the
    current chain, advances to the next in the list.

    If `interactive` is True, returns output on stdout and runs the next plugin
    synchronously."""

    if requirements is None:
        requirements = set()
    if done_requirements is None:
        done_requirements = set()
    restarted = False
    if isinstance(chains, basestring):
        raise NotImplementedError("API changed.")
    chain = chains[0]
    try:
        _run_plugin(context, chain, plugin_name, requirements, interactive,
                    done_requirements, outputs)
    except plugin.Restart as e:
        if restarts > 0:
            jitter = random.randint(30, 90)
            after = timedelta(seconds=jitter)
            run = _select_run_method(context, interactive, run_plugin, after)
            run(context, plugin_name, requirements, interactive,
                done_requirements, restarts=restarts - 1)
            restarted = True
        else:
            if outputs:
                stdout, stdout_verbose, stderr = outputs
            else:
                stderr = output.get(interactive, err=True)
            stderr(
                "Exceeded allowed number of restarts in plugin '{}' for "
                "'{}': {}".format(plugin_name, _get_uid(context), unicode(e)),
                end='\n',
            )
    finally:
        if not restarted:
            run_next_plugin(context, chains, requirements, interactive,
                            done_requirements, outputs)


def _run_plugin(context, chain, plugin_name, requirements, interactive,
                done_requirements, outputs=None):
    if outputs:
        stdout, stdout_verbose, stderr = outputs
    else:
        stdout = output.get(interactive)
        stderr = output.get(interactive, err=True)

    message = "[{}] {}... ".format(plugin_name, _get_uid(context))
    stdout(message, end='')
    new_context = {}
    try:
        is_up, message, new_context = plugin.run(chain, plugin_name,
                                                 **context)
    except plugin.Restart as e:
        stdout('needs to be restarted: {}'.format(unicode(e)))
        raise
    except Exception:
        stdout('', end='\r')
        stderr(
            "{}\nException in plugin '{}' for '{}'.".format(
                traceback.format_exc(),
                plugin_name,
                _get_uid(context),
            ),
            end='\n',
        )
        raise
    else:
        if message:
            stdout(message, verbose=not is_up)
        if is_up:
            requirements.add(plugin_name)
            context['successful_plugins'] = ', '.join(sorted(requirements))
        context.update(new_context)
    finally:
        done_requirements.add(plugin_name)


def _run_chain(context, chain_name, requirements=None, interactive=False,
               done_requirements=None, outputs=None):
    if requirements is None:
        requirements = set()
    if done_requirements is None:
        done_requirements = set()
    to_run = plugin.next(chain_name, requirements) - done_requirements
    if not to_run:
        return
    plugin_name = plugin.highest_priority(chain_name, to_run)
    try:
        _run_plugin(context, chain_name, plugin_name, requirements,
                    interactive, done_requirements, outputs)
    finally:
        run_chain(context, chain_name, requirements, interactive,
                  done_requirements, outputs)


def _get_uid(context):
    """Returns a unique context identifier for logging purposes for a plugin.
    """

    if 'uid' in context:
        return context['uid']
    return context.get('ip', '')


def _select_run_method(context, interactive, function, after):
    """Return a function that either executes the task directly (if
    `interactive` is True), enqueues it right away or schedules its enqueueing
    (if `after` is given).
    """

    if interactive:
        return function
    set_queue(context)
    if after:
        # FIXME: what about timeout= and result_ttl= for scheduled tasks?
        scheduler = django_rq.get_scheduler(context['queue'], )
        if isinstance(after, timedelta):
            enqueue = scheduler.enqueue_in
        elif isinstance(after, datetime):
            enqueue = scheduler.enqueue_at
        else:
            raise NotImplementedError(
                "after={!r} not supported.".format(after),
            )
        return partial(enqueue, after, function)
    queue = django_rq.get_queue(
        context['queue'],
    )
    return partial(_enqueue, queue, function)


def _enqueue(queue, function, *args, **kwargs):
    queue.enqueue_call(
        func=function,
        args=args,
        kwargs=kwargs,
        timeout=SINGLE_DISCOVERY_TIMEOUT,
        result_ttl=0,
    )


def discover_address(address, requirements=None, interactive=True, queue=None):
    if queue is None:
        try:
            net = Network.from_ip(address)
        except IndexError:
            raise NoQueueError(
                "Address {0} doesn't belong to any configured "
                "environment.".format(address),
            )
        if not net.environment or not net.environment.queue:
            raise NoQueueError(
                "The network environment {0} has no discovery queue.".format(
                    net,
                ),
            )
        queue = net.environment.queue.name
    run_next_plugin(
        {'ip': address, 'queue': queue},
        ('discovery', 'postprocess'),
        requirements=requirements,
        interactive=interactive,
    )


def discover_network(network, plugin_name='ping', requirements=None,
                     interactive=False, update_existing=False, outputs=None):
    """Runs discovery for a single `network`. The argument may be
    an IPv[46]Network instance, a Network instance or a string
    holding a network address or a network name defined in the database.
    If `interactive` is False all output is omitted and discovery is done
    asynchronously by pushing tasks to Rabbit.
    If `update_existing` is True, only existing IPs from the specified
    network are updated.
    """
    sanity_check()
    if outputs:
        stdout, stdout_verbose, stderr = outputs
    else:
        stdout = output.get(interactive)
    dbnet = None
    if isinstance(network, (IPv4Network, IPv6Network)):
        net = network
        try:
            dbnet = Network.objects.get(address=str(network))
        except Network.DoesNotExist:
            pass
    elif isinstance(network, Network):
        net = network.network
        dbnet = network
    else:
        try:
            network = Network.objects.get(address=network)
        except Network.DoesNotExist:
            network = Network.objects.get(name=network)
            # if raises DoesNotExist here then so be it, user passed
            # a non-existent network.
        net = network.network
        dbnet = network
    if not dbnet or not dbnet.environment or not dbnet.environment.queue:
        # Only do discover on networks that have a queue defined.
        stdout(
            "Skipping network {} -- no queue defined for this network "
            "environment.".format(net),
        )
        return
    queue_name = dbnet.environment.queue.name
    stdout("Scanning network {} started.".format(net))
    if update_existing:
        ip_address_queryset = IPAddress.objects.filter(
            number__gt=int(net.ip), number__lt=int(net.broadcast))
        hosts = (i.address for i in ip_address_queryset)
    else:
        hosts = net.iterhosts()
    for host in hosts:
        discover_address(host, requirements, interactive, queue_name)
    if interactive:
        stdout()
    else:
        stdout('Scanning network {} finished.'.format(net))


def discover_all(interactive=False, update_existing=False, outputs=None):
    """Runs discovery on all networks defined in the database."""
    sanity_check()
    if outputs:
        stdout, stdout_verbose, stderr = outputs
    else:
        stdout = output.get(interactive)
    nets = Network.objects.filter(
        environment__isnull=False,
        environment__queue__isnull=False,
    )
    for net in nets:
        if interactive:
            discover_network(
                net.network,
                interactive=True,
                update_existing=True,
            )
        else:
            queue = django_rq.get_queue()
            queue.enqueue(
                discover_network,
                net.network,
                update_existing=update_existing,
            )
    stdout()
