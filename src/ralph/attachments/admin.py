from ralph.attachments.views import AttachmentsView


class AttachmentsMixin(object):
    """
    Mixin add new URL to admin for download file.
    """

    def __init__(self, *args, **kwargs):
        # create unique AttachmentsView subclass for each descendant admin site
        # this prevents conflicts between urls etc.
        # See ralph.admin.extra.RalphExtraViewMixin.post_register for details
        if self.change_views is None:
            self.change_views = []
        self.change_views.append(
            type(
                "{}AttachmentsView".format(self.__class__.__name__),
                (AttachmentsView,),
                {},
            )
        )
        super().__init__(*args, **kwargs)
