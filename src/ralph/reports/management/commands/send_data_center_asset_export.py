import logging
import mimetypes

from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.management import BaseCommand, CommandError
from django.core.validators import EmailValidator

from ralph.reports.resources import DataCenterAssetTextResource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    SUPPORTED_FORMATS = [".csv", ".xlsx", ".ods"]
    email_validator = EmailValidator()

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--output-format",
            type=str,
            default=".xlsx",
            help="Format of the resulting report file",
        )

        parser.add_argument(
            "--recipient-email", type=str, help="Recipient's email address"
        )

        parser.add_argument("--sender-email", type=str, help="Sender's email address")

    def handle(self, *args, **options):
        try:
            self._validate_options(options)
            output_format = options.get("output_format")
            recipient_email = options.get("recipient_email")
            sender_email = options.get("sender_email")
            dataset = DataCenterAssetTextResource().export()
            attachment_content = getattr(dataset, output_format[1:])
            attachment_mimetype = mimetypes.types_map[output_format]
            attachment_filename = "report" + output_format
            subject = "Ralph Data Center Asset Export"
            body = "Attached to this message is a dump " "of Ralph Data Center Assets"
            send_email_with_attachment(
                sender_email,
                recipient_email,
                subject,
                body,
                attachment_content,
                attachment_filename,
                attachment_mimetype,
            )
        except Exception:
            logger.error(
                "A problem with Data Center Asset Email Report occurred. "
                "Email report has not been sent."
            )
            raise

    def _validate_options(self, options):
        if options.get("output_format", None) not in self.SUPPORTED_FORMATS:
            raise CommandError(
                "Format has to be one of the following formats: {}".format(
                    ", ".join(self.SUPPORTED_FORMATS)
                )
            )

        checking = ""
        try:
            checking = "recipient-email"
            self.email_validator(options.get("recipient_email", None))
            checking = "sender-email"
            self.email_validator(options.get("sender_email", None))
        except ValidationError as e:
            raise CommandError("{}: {}".format(checking, e.message))


def send_email_with_attachment(
    sender_email,
    recipient_email,
    subject,
    body,
    attachment_content,
    attachment_filename,
    attachment_mimetype,
):
    email = EmailMessage(
        subject=subject, body=body, from_email=sender_email, to=[recipient_email]
    )
    email.attach(
        content=attachment_content,
        filename=attachment_filename,
        mimetype=attachment_mimetype,
    )
    email.send()
