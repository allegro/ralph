from django.contrib import messages


class ActiveDeploymentMessageMixin(object):
    def changeform_view(self, request, object_id, *args, **kwargs):
        return super().changeform_view(request, object_id, *args, **kwargs)
