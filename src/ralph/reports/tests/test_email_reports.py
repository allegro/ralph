import mimetypes
from unittest import mock

from ddt import data, ddt, unpack
from django.core import management
from django.core.management import CommandError

from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.tests import RalphTestCase

EXAMPLE_EMAIL = "example@example.com"


@ddt
class TestEmailReports(RalphTestCase):
    def setUp(self):
        DataCenterAssetFactory.create_batch(10)

    def call_command(
        self,
        output_format=".csv",
        recipient_email=EXAMPLE_EMAIL,
        sender_email=EXAMPLE_EMAIL,
    ):
        management.call_command(
            "send_data_center_asset_export",
            output_format=output_format,
            recipient_email=recipient_email,
            sender_email=sender_email,
        )

    @unpack
    @data(
        (
            {"recipient_email": "this_is_not_an_email"},
            "recipient-email: Enter a valid email address.",
        ),
        (
            {"sender_email": "this_is_not_an_email"},
            "sender-email: Enter a valid email address.",
        ),
    )
    def test_data_center_asset_report_validates_recipient_email(
        self, command_kwargs, error_message
    ):
        with self.assertRaises(CommandError) as error:
            self.call_command(**command_kwargs)
            self.assertEqual(error_message, error)

    @data(".csv", ".ods", ".xlsx")
    @mock.patch(
        "ralph.reports.management.commands."
        "send_data_center_asset_export.send_email_with_attachment"
    )
    def test_data_center_asset_report_expected_formats(
        self, output_format, send_email_with_attachment
    ):
        mimetype = mimetypes.types_map[output_format]
        filename = "report" + output_format
        self.call_command(output_format=output_format)

        call_args = send_email_with_attachment.call_args[0]

        self.assertEqual(EXAMPLE_EMAIL, call_args[0])
        self.assertEqual(EXAMPLE_EMAIL, call_args[1])
        self.assertEqual(filename, call_args[5])
        self.assertEqual(mimetype, call_args[6])
