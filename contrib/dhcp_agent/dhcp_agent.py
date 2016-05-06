#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import errno
import fcntl
import hashlib
import logging
import os
import subprocess
import sys
import tempfile
from optparse import OptionParser
from logging import handlers as logging_handlers

IS_PY3 = sys.version_info[0] == 3
if IS_PY3:
    from dbm import gnu as gdbm
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    from urllib.error import HTTPError
else:
    import gdbm
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError


MODES = ('all', 'networks', 'entries')
MODE_ALL, MODE_NETWORKS, MODE_ENTRIES = MODES
MODES_EXCLUDE_ALL = set(MODES) - set([MODE_ALL])

PROTOS = ('http', 'https')
PROTO_HTTP, PROTO_HTTPS = PROTOS

CONFIG_HTTP_LAST_MODIFIED = 'http-last-modified'
DEFAULT_DHCP_SERVICE_NAME = 'isc-dhcp-server'


def _get_cmd_parser():
    parser = OptionParser(
        description='Update configuration in DHCP server.',
    )
    parser.add_option('-H', '--host', help='Ralph instance host.')
    parser.add_option('-k', '--key', help='Ralph API key.')
    parser.add_option(
        '-m',
        '--mode',
        type='choice',
        choices=MODES,
        default=MODE_ALL,
        help='Choose what part of config you want to upgrade. '
             '[Default: all; Options: {}]'.format(', '.join(MODES)),
    )
    parser.add_option(
        '-l',
        '--log-path',
        help='Path to log file. [Default: STDOUT]',
        default='STDOUT',
    )
    parser.add_option(
        '-c',
        '--dhcp-config-entries',
        help='Path to the DHCP entries configuration file.',
    )
    parser.add_option(
        '-n',
        '--dhcp-config-networks',
        help='Path to the DHCP networks configuration file.',
    )
    parser.add_option(
        '-a',
        '--proto',
        type='choice',
        choices=PROTOS,
        default=PROTO_HTTPS
    )
    parser.add_option(
        '-e',
        '--net-env',
        help='Only get config for the specified network environment.',
    )
    parser.add_option(
        '-d',
        '--dc',
        help='Only get config for the specified data center.',
    )
    parser.add_option(
        '-r',
        '--restart',
        help='Restart service after fetch config?',
        action='store_true',
    )
    parser.add_option(
        '-v',
        '--verbose',
        help='Increase verbosity.',
        action='store_true',
        default=False,
    )
    parser.add_option(
        '-s',
        '--dhcp-service-name',
        help='Name of the service to restart.',
        default=DEFAULT_DHCP_SERVICE_NAME
    )
    return parser


def _setup_logging(filename, verbose=False):
    log_size = 20  # MB
    logger = logging.getLogger(__file__)
    if verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    if not filename or filename in ('-', 'STDOUT'):
        handler = logging.StreamHandler()
    else:
        handler = logging_handlers.RotatingFileHandler(
            filename, maxBytes=(log_size * (1 << 20)), backupCount=5
        )
    fmt = logging.Formatter("[%(asctime)-12s.%(msecs)03d] "
                            "%(levelname)-8s %(filename)s:%(lineno)d  "
                            "%(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(fmt)

    logger.addHandler(handler)
    return logger


def _remove_apication_lock(lockfile, logger):
    logger.info('Remove lock')
    os.unlink(lockfile)


def _set_script_lock(logger):
    lockfile = '{}.lock'.format(
        os.path.join(tempfile.gettempdir(), os.path.split(sys.argv[0])[1])
    )
    f = os.open(lockfile, os.O_TRUNC | os.O_CREAT | os.O_RDWR)
    try:
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(f, '{}'.format(os.getpid()).encode())
        atexit.register(_remove_apication_lock, lockfile, logger)
    except IOError as e:
        if e.errno == errno.EAGAIN:
            logger.critical('Script already running.')
            sys.exit(2)
        raise


def _get_cmd_params_from_parser(parser):
    """The wrapper to parser which returned dict instead of tuple.

    Returns:
        dict: The dictonary contains pairs - option and option's value.
    """
    return vars(parser.parse_args()[0])


def _check_params(params, error_callback):
    """
    Returns:
        bool: True if all conditions are
    """
    required_params = {'host', 'key'}
    diff = required_params - {k for k, v in params.items() if v}
    if diff:
        error_callback('ERROR: {} are required.'.format(
            ', '.join(['--{}'.format(d) for d in diff]))
        )
        return False

    dc = params.get('dc')
    net_env = params.get('net_env')
    if (dc and net_env) or (not dc and not net_env):
        error_callback(
            'ERROR: Only DC or ENV mode available.',
        )
        return False
    return True


class DHCPConfigManager(object):
    def __init__(
        self, logger, host, key, dc=None, net_env=None, mode=MODE_ALL,
        verbose=False, restart=False, proto=PROTO_HTTPS,
        dhcp_config_entries='', dhcp_config_networks='',
        dhcp_service_name=DEFAULT_DHCP_SERVICE_NAME, **kwargs
    ):
        self.load_config()
        self.logger = logger
        self.host = host
        self.key = key
        self.proto = proto
        self.can_restart_dhcp_server = restart
        self.dhcp_service_name = dhcp_service_name
        self.dhcp_entries_config_path = dhcp_config_entries
        self.dhcp_networks_config_path = dhcp_config_networks
        self.envs = net_env.split(',') if net_env else []
        self.dcs = dc.split(',') if dc else []
        self.mode = mode

    def download_and_apply_configuration(self):
        request_params = self.get_request_params(self.dcs, self.envs)
        should_restart_dhcp_server = False
        if self.mode == MODE_ALL:
            fetch_statuses = []
            for m in MODES_EXCLUDE_ALL:
                fetch_statuses.append(self.fetch_configuration(
                    m, request_params
                ))
            should_restart_dhcp_server = any(fetch_statuses)
        else:
            should_restart_dhcp_server = self.fetch_configuration(
                self.mode, request_params
            )

        if self.can_restart_dhcp_server and should_restart_dhcp_server:
            self._restart_dhcp_server()
        self._send_synch_confirmation()
        self.save_config()

    def make_request(self, url, data=None):
        data = urlencode(data).encode('utf-8') if data else None
        headers = {}
        last = self.get_last_modified(url)
        if last:
            headers['If-Modified-Since'] = last
        headers.update({'Authorization': 'Token {}'.format(self.key)})
        return urlopen(Request(url, data=data, headers=headers))

    def load_config(self):
        config_dir = os.path.expanduser('~/.ralph-dhcp-agent')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        config_file = os.path.join(config_dir, 'config.db')
        self._config = gdbm.open(config_file, 'c')

    def save_config(self):
        self._config.close()

    def get_url_hash(self, url):
        hash_url = hashlib.md5()
        hash_url.update(url.encode())
        return hash_url.hexdigest()

    def get_last_modified(self, url):
        h = self.get_url_hash(url)
        try:
            last = self._config[CONFIG_HTTP_LAST_MODIFIED + h]
        except KeyError:
            last = None
        return last

    def set_last_modified(self, url, value):
        h = self.get_url_hash(url)
        self._config[CONFIG_HTTP_LAST_MODIFIED + h] = value

    def fetch_configuration(self, mode, request_params):
        is_saved = False
        dhcp_config = self._get_configuration(mode, request_params)
        if dhcp_config:
            is_saved = self._set_new_configuration(
                dhcp_config, mode
            )
        return all([dhcp_config, is_saved])

    def get_request_params(self, dcs, envs):
        request_params = []
        if envs:
            request_params.extend([('env', env) for env in envs])
        if dcs:
            request_params.extend([('dc', dc) for dc in dcs])
        assert request_params != []
        return request_params

    def _get_configuration(self, mode, params):
        url = '{}://{}/dhcp/{}/?{}'.format(
            self.proto,
            self.host,
            mode,
            urlencode(params)
        )
        configuration = None

        self.logger.info('Sending request to {}'.format(url))
        try:
            response = self.make_request(url)
        except HTTPError as e:
            if e.code != 304:
                self.logger.error(
                    'Server returned {} status code with message "{}"'.format(
                        e.code, e.fp.read().decode()
                    )
                )
            else:
                self.logger.info(
                    'Server return status 304 NOT MODIFIED. Nothing to do.'
                )
            return False
        else:
            configuration = response.read()
            self.set_last_modified(url, response.headers.get('Last-Modified'))
        return configuration

    def _send_synch_confirmation(self):
        """This method notify Ralph about restarting DHCP server with
        new configuration.

        Returns:
            bool: True if server returns 200 status code, otherwise False
        """
        url = '{}://{}/dhcp/synch/'.format(
            self.proto,
            self.host,
        )
        try:
            self.make_request(url, data={})
        except HTTPError as e:
            self.logger.error(
                'Could not send confirmation to Ralph. '
                'Server returned {} status code with message: {}'.format(
                    e.code, e.fp.read().decode()
                ),
            )
            return False
        self.logger.info('Confirmation sent to {}.'.format(self.host))
        return True

    def _set_new_configuration(self, config, mode):
        """The method writing (or printing) config file.

        Args:
            config (string): The plain text contains raw configuration
                for DHCP server,
            mode (string): The choice from MODES_EXCLUDE_ALL.

        Returns:
            bool: True if config saved successfully, otherwise False
        """
        config_path = getattr(self, 'dhcp_{}_config_path'.format(mode))
        try:
            if config_path:
                with open(config_path, 'w') as f:
                    f.write(config)
                self.logger.info(
                    'Configuration written to {}'.format(config_path)
                )
            else:
                sys.stdout.write(config.decode())
                self.logger.info('Configuration written to stdout.')
            return True
        except IOError as e:
            self.logger.error(
                'Could not write new DHCP configuration. Error '
                'message: {}'.format(e),
            )
            return False

    def _restart_dhcp_server(self):
        """The method restarting DHCP server.

        Returns:
            bool: True if DHCP server restarted successfully, otherwise False
        """
        self.logger.info('Restarting {}...'.format(self.dhcp_service_name))
        command = ['service', self.dhcp_service_name, 'restart']
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        proc.wait()
        restart_successful = proc.returncode == 0
        if restart_successful:
            self.logger.info(
                'Service {} successfully restarted.'.format(
                    self.dhcp_service_name
                )
            )
        else:
            self.logger.error(
                'Failed to restart service {}.'.format(self.dhcp_service_name)
            )
        return restart_successful


def main():
    parser = _get_cmd_parser()
    params = _get_cmd_params_from_parser(parser)
    _check_params(params, parser.error)

    logger = _setup_logging(params['log_path'], params['verbose'])
    _set_script_lock(logger)
    dhcp_manager = DHCPConfigManager(logger=logger, **params)
    dhcp_manager.download_and_apply_configuration()


if __name__ == '__main__':
    main()
