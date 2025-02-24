#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import contextlib
import errno
import fcntl
import hashlib
import logging
import os
import subprocess
import sys
import tempfile
from logging import handlers as logging_handlers
from optparse import OptionParser

IS_PY3 = sys.version_info[0] == 3
if IS_PY3:
    from dbm import gnu as cache_db
    from urllib.error import HTTPError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
    string_types = (str,)
else:
    import dbm as cache_db
    from urllib import urlencode

    from urllib2 import HTTPError, Request, urlopen
    string_types = (basestring,)


APP_DIR = os.path.expanduser('~/.ralph-dhcp-agent')

PROTOS = ('http', 'https')
PROTO_HTTP, PROTO_HTTPS = PROTOS

CACHE_LAST_MODIFIED_PREFIX = 'http-last-modified'
DEFAULT_DHCP_SERVICE_NAME = 'isc-dhcp-server'


@contextlib.contextmanager
def open_file_or_stdout_to_writing(filename=None):
    """Context manager opens file or stdout and returns its handle."""
    if filename in ['-', None]:
        handler = sys.stdout
    else:
        handler = open(filename, 'w')
    try:
        yield handler
    finally:
        if handler is not sys.stdout:
            handler.close()


class Cache(object):
    """Simple key-value cache based on dbm."""
    def __init__(self, cache_path):
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        self._cache = cache_db.open(os.path.join(cache_path, 'cache'), 'c')

    def get(self, key, prefix=''):
        url_hash = get_url_hash(key)
        try:
            last = self._cache[prefix + url_hash]
        except KeyError:
            last = None
        return last

    def set(self, key, value, prefix=''):
        url_hash = get_url_hash(key)
        self._cache[prefix + url_hash] = value

    def close(self):
        self._cache.close()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


def get_url_hash(url):
    hash_url = hashlib.md5()
    hash_url.update(url.encode())
    return hash_url.hexdigest()


def convert_to_request_params(params):
    """Convert dict with into flat list.

    Example:
        >>> convert_to_request_params({'foo': ['bar1', 'bar2']})
        [('foo': 'bar1'), ('foo', 'bar2')]
        >>> convert_to_request_params({'foo': 'bar1'})
        [('foo': 'bar1')]

    Returns:
        list: list contains key-value pairs
    """
    request_params = []
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            request_params.extend([(key, param) for param in value])
        if isinstance(value, string_types):
            request_params.extend([(key, value)])
    return request_params


def _get_cmd_parser():
    parser = OptionParser(
        description='Update configuration in DHCP server.',
    )
    parser.add_option('-H', '--host', help='Ralph instance host.')
    parser.add_option('-k', '--key', help='Ralph API key.')
    parser.add_option(
        '-m',
        '--sections',
        type='choice',
        choices=DHCPConfigManager.DHCP_SECTIONS,
        action='append',
        help='Choose what part of config you want to upgrade. '
             '[Default: all; Options: {}]'.format(', '.join(DHCPConfigManager.DHCP_SECTIONS)),  # noqa
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
        '-p',
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
        help='Restart service after fetching config?',
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
    log_size = os.getenv('DHCP_AGENT_LOG_SIZE', 20)  # MB
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


def _remove_application_lock(lockfile, logger):
    logger.info('Removing lock')
    os.unlink(lockfile)


def _set_script_lock(logger):
    lockfile = '{}.lock'.format(
        os.path.join(tempfile.gettempdir(), os.path.split(sys.argv[0])[1])
    )
    f = os.open(lockfile, os.O_TRUNC | os.O_CREAT | os.O_RDWR)
    try:
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(f, '{}'.format(os.getpid()).encode())
        atexit.register(_remove_application_lock, lockfile, logger)
    except IOError as e:
        if e.errno == errno.EAGAIN:
            logger.critical('Script already running.')
            sys.exit(2)
        raise


def _get_cmd_params_from_parser(parser):
    """Wrapper around parser returning a dict instead of a tuple.

    Returns:
        dict: The dictonary contains pairs - option and option's value.
    """
    return vars(parser.parse_args()[0])


def _check_params(params, error_callback):
    """Predicate function returning bool depending on conditions.

    List of conditions:
        - `host` and `key` must be specified in params,
        - `dc` or `env` must be specified in params,
        - `sections` must be specified in params.

    Returns:
        bool: True if all conditions are met, False otherwise
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
    sections = params.get('sections')
    if not sections:
        error_callback(
            'ERROR: option `sections` are required.',
        )
        return False
    return True


class DHCPConfigManager(object):
    """Manager responsible for fetching configuration and restarting
    DHCP server.
    """

    DHCP_SECTIONS = ('networks', 'entries')

    def __init__(
        self, logger, cache, host, key, sections, dc=None, net_env=None,
        verbose=False, restart=False, proto=PROTO_HTTPS,
        dhcp_config_entries=None, dhcp_config_networks=None,
        dhcp_service_name=DEFAULT_DHCP_SERVICE_NAME,
        **kwargs
    ):
        self.cache = cache
        self.logger = logger
        self.host = host
        self.key = key
        self.proto = proto
        self.can_restart_dhcp_server = restart
        self.dhcp_service_name = dhcp_service_name
        self.envs = net_env.split(',') if net_env else []
        self.dcs = dc.split(',') if dc else []
        self.sections = sections
        self.section_config_path_mapper = {
            'entries': dhcp_config_entries,
            'networks': dhcp_config_networks,
        }

    def download_and_apply_configuration(self):
        should_restart_dhcp_server = False
        successful_list = []
        for section in self.sections:
            is_saved = False
            dhcp_config = self._get_configuration(section)
            if dhcp_config:
                is_saved = self._set_new_configuration(
                    dhcp_config, self.section_config_path_mapper[section]
                )
                successful_list.append(is_saved)
        should_restart_dhcp_server = any(successful_list)

        if self.can_restart_dhcp_server and should_restart_dhcp_server:
            self._restart_dhcp_server()
        self._send_sync_confirmation()

    def make_authorized_request(self, url):
        """Make request with extra headers like Authorization
        and If-Modified-Since.

        Headers send with request:
            - Authorization: contains token for autorization on the server,
            - If-Modified-Since: information for server about configuration's
                last date.

        Returns:
            object: standard response object (file-like object)
        """
        headers = {}
        last = self.cache.get(prefix=CACHE_LAST_MODIFIED_PREFIX, key=url)
        if last:
            self.logger.info(
                'Using If-Modified-Since with value {} for url {}'.format(
                    last, url
                )
            )
            headers['If-Modified-Since'] = last
        else:
            self.logger.info(
                'Last modified not found in cache for url {}'.format(url)
            )
        headers.update({'Authorization': 'Token {}'.format(self.key)})
        return urlopen(Request(url, headers=headers))

    def _get_configuration(self, mode):
        """Fetches configuration for DHCP server from Ralph server."""
        params = convert_to_request_params({'dc': self.dcs, 'env': self.envs})
        url = '{}://{}/dhcp/{}/'.format(
            self.proto,
            self.host,
            mode,
        )
        if params:
            params = urlencode(params)
            url += '?' + params
        configuration = None

        self.logger.info('Sending request to {}'.format(url))
        try:
            response = self.make_authorized_request(url)
        except HTTPError as e:
            if e.code != 304:
                self.logger.error(
                    'Server returned %s status code with message "%s"',
                    e.code, e.fp.read().decode()
                )
            else:
                self.logger.info(
                    'Server return status 304 NOT MODIFIED. Nothing to do.'
                )
            return False
        else:
            configuration = response.read()
            last_modified = response.headers.get('Last-Modified')
            self.logger.info(
                'Storing Last-Modified for url {} with value {}'.format(
                    url, last_modified
                )
            )
            self.cache.set(
                prefix=CACHE_LAST_MODIFIED_PREFIX,
                key=url,
                value=last_modified
            )
        return configuration

    def _send_sync_confirmation(self):
        """This method notifies Ralph about restarting DHCP server with
        new configuration.

        Returns:
            bool: True if server returns 200 status code, otherwise False
        """
        url = '{}://{}/dhcp/sync/'.format(
            self.proto,
            self.host,
        )
        try:
            self.make_authorized_request(url)
        except HTTPError as e:
            self.logger.error(
                'Could not send confirmation to Ralph. '
                'Server returned %s status code with message: %s',
                e.code, e.fp.read().decode()
            )
            return False
        self.logger.info('Confirmation sent to {}.'.format(self.host))
        return True

    def _set_new_configuration(self, config, path_to_config=None):
        """Writes (or prints) config file.

        Args:
            config (string): Raw (i.e., in plain text) configuration for
                DHCP server,
            path_to_config (string): The path to config file.

        Returns:
            bool: True if config is saved successfully, otherwise False
        """
        try:
            with open_file_or_stdout_to_writing(path_to_config) as f:
                f.write(str(config))
                self.logger.info(
                    'Configuration written to {}'.format(
                        path_to_config or 'stdout'
                    )
                )
            return True
        except IOError as e:
            self.logger.error(
                'Could not write new DHCP configuration. Error message: %s',
                e
            )
            return False

    def _restart_dhcp_server(self):
        """Restarts DHCP server.

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
                'Failed to restart service %s.', self.dhcp_service_name
            )
        return restart_successful


def main():
    parser = _get_cmd_parser()
    params = _get_cmd_params_from_parser(parser)
    _check_params(params, parser.error)

    logger = _setup_logging(params['log_path'], params['verbose'])
    _set_script_lock(logger)
    with Cache(APP_DIR) as cache:
        dhcp_manager = DHCPConfigManager(cache=cache, logger=logger, **params)
        dhcp_manager.download_and_apply_configuration()


if __name__ == '__main__':
    main()
