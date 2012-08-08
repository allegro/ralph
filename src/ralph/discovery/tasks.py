#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Celery task for discovery."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import textwrap
import traceback

from celery.task import task
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from ipaddr import IPv4Network, IPv6Network

from ralph.discovery.models import Network, IPAddress
from ralph.util.network import ping
from ralph.util import output, plugin


DNS_TXT_ATTRIBUTE_REGEX = re.compile(r'(?P<attribute>[^:]+): (?P<value>.*)')
MAX_RESTARTS = 3
SANITY_CHECK_PING_ADDRESS = settings.SANITY_CHECK_PING_ADDRESS
NETWORK_TASK_DELEGATION_TIMEOUT = settings.NETWORK_TASK_DELEGATION_TIMEOUT
SINGLE_DISCOVERY_TIMEOUT = settings.SINGLE_DISCOVERY_TIMEOUT

class DCRouter(object):
    """Route the discovery tasks to the right data center for them.
       Use the default queue if no network matches the IP address."""

    def route_for_task(self, task, args=None, kwargs=None):
        if task == 'ralph.discovery.tasks.run_chain':
            return args[1] or 'celery'
        if task != 'ralph.discovery.tasks.discover_single':
            return 'celery'
        try:
            queue = args[0]['queue']
        except KeyError:
            try:
                net = Network.from_ip(args[0]['ip'])
                queue = net.queue or net.data_center.name
            except (IndexError, KeyError):
                queue = 'celery'
            args[0]['queue'] = queue
        return queue

def sanity_check(perform_network_checks=True):
    """Checks configuration integrity by pinging www.allegro.pl."""
    if not perform_network_checks:
        return

    if ping(SANITY_CHECK_PING_ADDRESS) is None:
        raise ImproperlyConfigured(textwrap.dedent("""
            fatal: {} is not pingable.

            Things you might want to check:
             * is this host connected to network
             * is this domain pingable from your terminal
             * is your python binary capped with setcap CAP_NET_RAW
               or
             * are you running tests from root
               or
             * are you using setuid bin/python""").strip().format(
                 SANITY_CHECK_PING_ADDRESS))

def _run_plugin(context, chain, plugin_name, requirements, interactive,
                clear_down, done_requirements, outputs=None):
    if outputs:
        stdout, stdout_verbose, stderr = outputs
    else:
        stdout = output.get(interactive)
        stdout_verbose = output.get(interactive, verbose=True)
        stderr = output.get(interactive, err=True)

    message = "[{}] {}... ".format(plugin_name, context.get('ip', ''))
    pad = output.WIDTH - len(message)
    stdout(message, end='')
    try:
        new_context = {}
        is_up, message, new_context = plugin.run(chain, plugin_name,
                                                 **context)
        if is_up:
            requirements.add(plugin_name)
    except plugin.Restart as e:
        stdout('needs to be restarted: {}'.format(unicode(e)), end='\n')
        raise
    except Exception:
        stdout('', end='\r')
        stderr("Exception in plugin '{}' for '{}': {}".format(
            plugin_name,
            context.get('ip', 'none'),
            traceback.format_exc()),
            end='\n')
    else:
        message = message or ''
        if clear_down and not is_up:
            end = '\r'
        else:
            end = '\n'
        pad -= len(message)
        message = message + (" " * pad)
        if is_up:
            stdout(message, end=end)
        else:
            stdout_verbose(message, end=end)
    finally:
        done_requirements.add(plugin_name)
    context.update(new_context)

def run_next_plugin(context, requirements=None, interactive=False,
                    clear_down=True, done_requirements=None, outputs=None):
    discover = discover_single
    if not interactive:
        discover = discover.delay
    to_run = plugin.next('discovery', requirements) - done_requirements
    if to_run:
        plugin_name = plugin.highest_priority('discovery', to_run)
        discover(context, plugin_name, requirements, interactive, clear_down,
                 done_requirements)
        return
    to_run = plugin.next('postprocess', requirements) - done_requirements
    for plugin_name in plugin.prioritize('postprocess', to_run):
        _run_plugin(context, 'postprocess', plugin_name, requirements,
                    interactive, clear_down, done_requirements, outputs)

@task(ignore_result=True, expires=3600)
def dummy_task(interactive=False, index=None):
    stdout = output.get(interactive)
    if index:
        stdout("Ping {}.".format(index))
    else:
        stdout("Ping.")

@task(ignore_result=True, expires=3600)
def dummy_horde(interactive=False, how_many=1000):
    if interactive:
        for i in xrange(how_many):
            dummy_task(interactive=interactive, index=i+1)
    else:
        for i in xrange(how_many):
            dummy_task.delay(interactive=interactive, index=i+1)


@task(ignore_result=True)
def run_chain(context, chain_name, requirements=None, interactive=False,
              clear_down=True, done_requirements=None, outputs=None):
    if requirements is None:
        requirements = set()
    if done_requirements is None:
        done_requirements = set()
    to_run = plugin.next(chain_name, requirements) - done_requirements
    if not to_run:
        return
    plugin_name = plugin.highest_priority(chain_name, to_run)
    _run_plugin(context, chain_name, plugin_name, requirements, interactive,
            clear_down, done_requirements, outputs)
    run_chain(context, chain_name, requirements, interactive, clear_down,
              done_requirements, outputs)


@task(ignore_result=True, expires=SINGLE_DISCOVERY_TIMEOUT)
def discover_single(context, plugin_name='ping', requirements=None,
    interactive=False, clear_down=True, done_requirements=None,
    restarts=MAX_RESTARTS, outputs=None):
    """
    Runs discovery on a single `ip`. If `interactive` is True, returns
    output on stdout. In that case, when `clear_down` is True (the default),
    lines listing addresses of hosts which are down are cleared from output.
    """
    if requirements is None:
        requirements = set()
    if done_requirements is None:
        done_requirements = set()
    restarted = False
    try:
        _run_plugin(context, 'discovery', plugin_name, requirements,
                    interactive, clear_down, done_requirements, outputs)
    except plugin.Restart as e:
        if restarts > 0:
            discover = discover_single
            if not interactive:
                discover = discover.delay
            discover(context, plugin_name, requirements, interactive,
                    clear_down, done_requirements, restarts=restarts-1)
            restarted = True
        else:
            if outputs:
                stdout, stdout_verbose, stderr = outputs
            else:
                stderr = output.get(interactive, err=True)
            stderr("Exceeded allowed number of restarts in plugin '{}' for "
                "'{}': {}".format(plugin_name, context['ip'], unicode(e)),
                end='\n')

    if not restarted:
        run_next_plugin(context, requirements, interactive, clear_down,
                        done_requirements, outputs)

def discover_single_synchro(ip):
    requirements = set()
    done_requirements = set()
    to_run = ['ping']
    context = {'ip': ip}

    messages = []
    def output(*args, **kwargs):
        messages.append(''.join(args))
        messages.append(kwargs.get('end', '\n'))
    outputs = (output, output, output)

    while to_run:
        messages[:] = []
        plugin_name = plugin.highest_priority('discovery', to_run)
        for retry in range(5):
            try:
                _run_plugin(context, 'discovery', plugin_name, requirements,
                            True, False, done_requirements, outputs)
            except plugin.Restart:
                pass
            else:
                break
        else:
            messages.append('Plugin failed after %d retries.\n' % retry)
        to_run = plugin.next('discovery', requirements) - done_requirements
        yield ''.join(messages)
        yield '\n'

    to_run = plugin.next('postprocess', requirements) - done_requirements
    for plugin_name in plugin.prioritize('postprocess', to_run):
        messages[:] = []
        _run_plugin(context, 'postprocess', plugin_name, requirements,
                    True, False, done_requirements, outputs)
        yield ''.join(messages)
        yield '\n'
    yield 'Finished.\n'


@task(ignore_result=True, time_limit=NETWORK_TASK_DELEGATION_TIMEOUT)
def discover_network(network, plugin_name='ping', requirements=None,
    interactive=False, update_existing=False, outputs=None):
    """Runs discovery for a single `network`. The argument may be
    an IPv[46]Network instance, a Network instance or a string
    holding a network address or a network name defined in the database.
    If `interactive` is False all output is omitted and discovery is done
    asynchronously by pushing tasks to Rabbit.
    If `update_existing` is True, only existing IPs from the specified
    network are updated."""
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
    stdout("Scanning network {} started.".format(net))
    if update_existing:
        ip_address_queryset = IPAddress.objects.filter(
            number__gt=int(net.ip), number__lt=int(net.broadcast))
        hosts = (i.address for i in ip_address_queryset)
    else:
        hosts = net.iterhosts()
    for index, host in enumerate(hosts):
        context = {'ip': host}
        if dbnet:
            context['queue'] = dbnet.queue

        if interactive:
            discover_single(context, plugin_name=plugin_name,
                requirements=requirements, interactive=True)
        else:
            discover_single.delay(context, plugin_name=plugin_name,
                requirements=requirements, clear_down=False)
    if interactive:
        stdout()
    else:
        stdout('Scanning network {} finished.'.format(net))

@task(ignore_result=True)
def discover_all(interactive=False, update_existing=False, outputs=None):
    """Runs discovery on all networks defined in the database."""
    sanity_check()
    if outputs:
        stdout, stdout_verbose, stderr = outputs
    else:
        stdout = output.get(interactive)
    for net in Network.objects.exclude(queue=None).exclude(queue=''):
        if interactive:
            discover_network(net.network, interactive=True,
                update_existing=True)
        else:
            discover_network.delay(net.network,
                update_existing=update_existing)
    stdout()
