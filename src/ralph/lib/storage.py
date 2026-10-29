import logging
import mimetypes
import tempfile

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


def _is_not_found(error):
    error_code = error.response.get("Error", {}).get("Code")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return error_code in ("404", "NoSuchKey", "NotFound") or status_code == 404


@deconstructible
class DualWriteS3Storage(Storage):
    """Keep media files on disk and in S3, with configurable read source."""

    def __init__(self):
        self.local_storage = FileSystemStorage()
        self._client = None

    @property
    def s3_enabled(self):
        return getattr(settings, "S3_STORAGE_ENABLED", False) or getattr(
            settings, "S3_SERVE_FILES", False
        )

    @property
    def serve_from_s3(self):
        return getattr(settings, "S3_SERVE_FILES", False)

    @property
    def serve_order(self):
        """Sources to read media from when S3 serving is enabled, in order of preference."""
        if getattr(settings, "PREFER_S3_FOR_MEDIA", False):
            return "s3", "disk"
        return "disk", "s3"

    def _first_available(self, name, **readers):
        """Return the result of the first reader, in serve order, that finds the file."""
        missing_in = []
        for source in self.serve_order:
            try:
                result = readers[source]()
            except FileNotFoundError as error:
                missing_in.append(source)
                not_found_error = error
                continue
            if missing_in:
                logger.warning(
                    "Media file %s is missing in %s, served from %s instead.",
                    name,
                    ", ".join(missing_in),
                    source,
                )
            return result
        raise FileNotFoundError(name) from not_found_error

    def _bucket_name(self):
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if not bucket:
            raise ImproperlyConfigured(
                "AWS_STORAGE_BUCKET_NAME must be configured to use S3 media storage."
            )
        return bucket

    def _get_s3_client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
                region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": getattr(settings, "AWS_S3_ADDRESSING_STYLE", "path")},
                ),
            )
        return self._client

    def _s3_exists(self, name):
        try:
            self._get_s3_client().head_object(Bucket=self._bucket_name(), Key=name)
        except ClientError as error:
            if _is_not_found(error):
                return False
            raise
        return True

    def _upload_fileobj(self, file_obj, name):
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        self._get_s3_client().upload_fileobj(
            file_obj,
            self._bucket_name(),
            name,
            ExtraArgs={"ContentType": content_type},
        )

    def _save(self, name, content):
        saved_name = self.local_storage.save(name, content)
        if not self.s3_enabled:
            return saved_name

        try:
            content.seek(0)
            self._upload_fileobj(content, saved_name)
        except Exception:
            # Do not leave a disk-only file that appears successfully saved in the DB.
            self.local_storage.delete(saved_name)
            raise
        return saved_name

    def _open(self, name, mode="rb"):
        if not self.serve_from_s3:
            return self.local_storage.open(name, mode)
        if mode not in ("r", "rb"):
            raise ValueError("S3 media files can only be opened for reading.")
        # Every write goes to both storages, so a file missing in one of them
        # (e.g. incomplete backfill or replication lag) can be served from the other.
        return self._first_available(
            name,
            disk=lambda: self.local_storage.open(name, mode),
            s3=lambda: self._open_s3(name),
        )

    def _open_s3(self, name):
        file_obj = tempfile.SpooledTemporaryFile(
            max_size=getattr(settings, "S3_FILE_SPOOL_MAX_SIZE", 8 * 1024 * 1024),
            mode="w+b",
        )
        try:
            self._get_s3_client().download_fileobj(self._bucket_name(), name, file_obj)
        except ClientError as error:
            file_obj.close()
            if _is_not_found(error):
                raise FileNotFoundError(name) from error
            raise
        except Exception:
            file_obj.close()
            raise
        file_obj.seek(0)
        return File(file_obj, name=name)

    def path(self, name):
        if self.serve_from_s3:
            raise NotImplementedError("S3 media files do not have a local filesystem path.")
        return self.local_storage.path(name)

    def url(self, name):
        if not self.serve_from_s3:
            return self.local_storage.url(name)
        return self._first_available(
            name,
            disk=lambda: self._local_url(name),
            # Not checked for existence to avoid an S3 request for every URL.
            s3=lambda: self._s3_url(name),
        )

    def _local_url(self, name):
        if not self.local_storage.exists(name):
            raise FileNotFoundError(name)
        return self.local_storage.url(name)

    def _s3_url(self, name):
        return self._get_s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket_name(), "Key": name},
            ExpiresIn=getattr(settings, "AWS_QUERYSTRING_EXPIRE", 3600),
        )

    def delete(self, name):
        if self.s3_enabled:
            self._get_s3_client().delete_object(Bucket=self._bucket_name(), Key=name)
        self.local_storage.delete(name)

    def exists(self, name):
        if self.local_storage.exists(name):
            return True
        return self.s3_enabled and self._s3_exists(name)

    def size(self, name):
        if not self.serve_from_s3:
            return self.local_storage.size(name)
        return self._first_available(
            name,
            disk=lambda: self.local_storage.size(name),
            s3=lambda: self._s3_size(name),
        )

    def _s3_size(self, name):
        try:
            response = self._get_s3_client().head_object(Bucket=self._bucket_name(), Key=name)
        except ClientError as error:
            if _is_not_found(error):
                raise FileNotFoundError(name) from error
            raise
        return response["ContentLength"]

    def get_available_name(self, name, max_length=None):
        return super().get_available_name(name, max_length=max_length)

    def listdir(self, path) -> tuple[list, list]:
        if not self.serve_from_s3:
            return self.local_storage.listdir(path)

        try:
            local_directories, local_files = self.local_storage.listdir(path)
        except FileNotFoundError:
            local_directories, local_files = [], []
        directories, files = set(local_directories), set(local_files)

        prefix = path.strip("/")
        if prefix:
            prefix += "/"
        paginator = self._get_s3_client().get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket_name(), Prefix=prefix, Delimiter="/"):
            directories.update(
                item["Prefix"][len(prefix) :].rstrip("/")
                for item in page.get("CommonPrefixes", [])
            )
            files.update(item["Key"][len(prefix) :] for item in page.get("Contents", []))
        return sorted(directories), sorted(files)

    def copy_local_to_s3(self, name) -> bool:
        """Copy a legacy local file to S3; return False if S3 already has it."""
        if self._s3_exists(name):
            return False
        if not self.local_storage.exists(name):
            raise FileNotFoundError(self.local_storage.path(name))

        with self.local_storage.open(name, "rb") as source:
            self._upload_fileobj(source, name)
        return True
