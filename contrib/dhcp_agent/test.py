import logging
import unittest
from optparse import Values

from dhcp_agent import (
    Cache,
    DHCPConfigManager,
    _check_params,
    _get_cmd_params_from_parser,
)
from mock import MagicMock, Mock, patch

logger = logging.getLogger(__file__)
mocked_parser = MagicMock()


def mocked_urlopen(*args):
    def mocked_read(self):
        return 'mocked'
    attrs = {
        'read': mocked_read,
        'headers': {'Last-Modified': ''}
    }
    return type('response', (object,), attrs)

def mocked_error(msg):
    raise Exception(msg)
mocked_parser.error = mocked_error

default_params = {
    'dhcp_config_entries': None,
    'verbose': False,
    'proto': 'http',
    'log_path': 'STDOUT',
    'restart': None,
    'dc': 'DC2',
    'host': '127.0.0.1:8000',
    'dhcp_config_networks': None,
    'sections': ['entries'],
    'key': '123',
    'dhcp_service_name': 'isc-dhcp-server',
    'net_env': None
}


class TestDHCPConfigManager(unittest.TestCase):

    @patch('optparse.OptionParser', mocked_parser)
    def test_get_cmd_params_from_parser_should_return_dict(self):
        mocked_parser.parse_args.return_value = (
            Values(default_params), None
        )
        returned_params = _get_cmd_params_from_parser(mocked_parser)
        self.assertEqual(type(returned_params), dict)

    @patch('optparse.OptionParser', mocked_parser)
    def test_empty_params_should_raise_exception(self):
        with self.assertRaises(Exception):
            _check_params({}, mocked_parser.error)

    @patch('optparse.OptionParser', mocked_parser)
    def test_env_end_dc_in_params_should_raise_exception(self):
        with self.assertRaises(Exception):
            _check_params(
                {
                    'key': 123,
                    'host': '127.0.0.1:8000',
                    'dc': 'DC1',
                    'net_env': 'test'
                }, mocked_parser.error
            )

    @patch('optparse.OptionParser', mocked_parser)
    def test_minmal_params(self):
        self.assertTrue(_check_params(
            {
                'key': 123,
                'host': '127.0.0.1:8000',
                'net_env': 'test',
                'sections': ['entries']
            }, mocked_parser.error
        ))
        self.assertTrue(_check_params(
            {
                'key': 123,
                'host': '127.0.0.1:8000',
                'dc': 'TEST',
                'sections': ['entries']
            }, mocked_parser.error
        ))

    @patch('dhcp_agent.urlopen')
    def test_main_command(self, mocked_urlopen):
        mock = Mock()
        mock.read.side_effect = ['resp1', 'resp2']
        mock.headers.get.return_value = ''
        mocked_urlopen.return_value = mock
        with Cache('/tmp/') as cache:
            dhcp_manager = DHCPConfigManager(
                cache=cache, logger=logger, **default_params
            )
            dhcp_manager.download_and_apply_configuration()


if __name__ == '__main__':
    unittest.main()
