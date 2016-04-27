import os
import unittest
import logging
from mock import patch, MagicMock
from optparse import Values

from dhcp_agent import _check_and_return_params, DHCPConfigManager

logger = logging.getLogger(__file__)

RALPH_KEY = os.getenv('RALPH_KEY', 'testkey')
RALPH_HOST = os.getenv('RALPH_HOST', '127.0.0.1:8000')

mocked_parser = MagicMock()


def mocked_error(msg):
    raise Exception(msg)
mocked_parser.error.side_effect = mocked_error

default_params = {
    'dhcp_config_entries': None,
    'verbose': False,
    'proto': 'http',
    'log_path': 'STDOUT',
    'restart': None,
    'dc': 'DC2',
    'host': RALPH_HOST,
    'dhcp_config_networks': None,
    'mode': 'entries',
    'key': RALPH_KEY,
    'dhcp_service_name': 'isc-dhcp-server',
    'net_env': None
}


class TestDHCPConfigManager(unittest.TestCase):
    @patch('optparse.OptionParser', mocked_parser)
    def test_required_params(self):
        mocked_parser.parse_args.return_value = (
            Values({
                'host': RALPH_HOST,
                'key': RALPH_KEY,
                'dc': 'DC1',
                'net_env': None,
            }), None
        )
        _check_and_return_params(mocked_parser)

    def test_request(self):
        manager = DHCPConfigManager(logger, **default_params)
        manager.run()


if __name__ == '__main__':
    unittest.main()
