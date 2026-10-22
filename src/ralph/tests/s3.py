import tempfile
from unittest.mock import patch

from botocore.exceptions import ClientError
from django.test import override_settings

from ralph.lib.storage import DualWriteS3Storage


def client_error(code, status_code, operation_name):
    return ClientError(
        {"Error": {"Code": code}, "ResponseMetadata": {"HTTPStatusCode": status_code}},
        operation_name,
    )


class FakeS3Client:
    """In-memory replacement for the boto3 S3 client used by DualWriteS3Storage."""

    def __init__(self):
        self.files = {}
        self.downloads = []
        self.upload_error = None
        self.download_error = None

    def upload_fileobj(self, file_obj, bucket, key, ExtraArgs=None):
        if self.upload_error:
            raise self.upload_error
        self.files[(bucket, key)] = file_obj.read()

    def download_fileobj(self, bucket, key, file_obj):
        self.downloads.append(key)
        if self.download_error:
            raise self.download_error
        try:
            content = self.files[(bucket, key)]
        except KeyError as error:
            raise client_error("404", 404, "HeadObject") from error
        file_obj.write(content)

    def head_object(self, Bucket, Key):
        try:
            content = self.files[(Bucket, Key)]
        except KeyError as error:
            raise client_error("404", 404, "HeadObject") from error
        return {"ContentLength": len(content)}

    def generate_presigned_url(self, operation, Params, ExpiresIn):
        return "https://s3.example.com/{}/{}?expires={}".format(
            Params["Bucket"], Params["Key"], ExpiresIn
        )

    def delete_object(self, Bucket, Key):
        self.files.pop((Bucket, Key), None)


class FakeS3StorageMixin:
    """
    Enable dual writes to an in-memory S3 client and keep local media files
    in a temporary MEDIA_ROOT for the duration of each test.
    """

    bucket = "media"

    def setUp(self):
        super().setUp()
        media_root = tempfile.TemporaryDirectory()
        self.addCleanup(media_root.cleanup)
        self.media_root = media_root.name

        settings_override = override_settings(
            MEDIA_ROOT=self.media_root,
            AWS_STORAGE_BUCKET_NAME=self.bucket,
            S3_STORAGE_ENABLED=True,
            S3_SERVE_FILES=False,
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.s3 = FakeS3Client()
        client_patch = patch.object(DualWriteS3Storage, "_get_s3_client", return_value=self.s3)
        client_patch.start()
        self.addCleanup(client_patch.stop)
