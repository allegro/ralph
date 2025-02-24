import mimetypes
import os
from collections import Iterable
from uuid import uuid4


def get_file_path(instance, filename, default_dir="attachments"):
    """Generates pseudo-random file path.

    Function generate hard to guess file path based on arguments and
    uuid4. In most cases is used in FileField as upload_to argument but
    you can use standalone as well.

    Args:
        instance: Model instance. Unused.
        filename: A original file name with extension.
        default_dir: Something like namespace for files. The

    Returns:
        A generated filename with schema:
            {attachment}/{1st_uuid_char}/{2nd_uuid_char}/{uuid}.{ext}
    """
    ext = os.path.splitext(filename)[1]
    name = "".join([str(uuid4()), ext])
    return os.path.join(default_dir, name[:1], name[1:2], name)


def add_attachment_from_disk(objs, local_path_to_file, owner, description=""):
    """Create attachment from absolute file path.

    Function create and returns attachment object with file from local path.

    Args:
        obj:
        local_path_to_file:
        owner:
        description:

    Returns:
        returns

    Raises:
        raises
    """
    """
    Function added file from disk as attachment and attach to object.

    Example:
    >>> # added /etc/passwd to foo by root
    >>> add_attachment_from_disk(foo, '/etc/passwd', root)
    """
    from ralph.attachments.models import Attachment, AttachmentItem

    attachment = Attachment.objects.create_from_file_path(local_path_to_file, owner)
    mime_type = mimetypes.guess_type(local_path_to_file)[0]
    if mime_type is None:
        mime_type = "application/octet-stream"
    attachment.mime_type = mime_type
    attachment.description = description
    attachment.save()
    if not isinstance(objs, Iterable):
        objs = [objs]
    for obj in objs:
        AttachmentItem.objects.refresh(obj, new_objects=[attachment])
    return attachment
