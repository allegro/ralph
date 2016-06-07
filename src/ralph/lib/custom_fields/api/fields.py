from rest_framework import serializers


class CustomFieldValueHyperlinkedIdentityField(
    serializers.HyperlinkedIdentityField
):
    """
    Hyperlink field to custom field value in context of particular object,
    ex. /api/somemodel/<object_pk>/customfields/<pk>
    """
    related_model_lookup_field = 'object_pk'

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {
            self.lookup_url_kwarg: lookup_value,
            # add additional related model pk - this is id of the current object
            # (in context)
            self.related_model_lookup_field: obj.object_id,
        }
        return self.reverse(
            # view_name is different for every model (usually
            # <modelname>-customfield-list or <modelname>-customfield-detail)
            view_name, kwargs=kwargs, request=request, format=format
        )
