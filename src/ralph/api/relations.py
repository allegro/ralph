from rest_framework import relations

from ralph.api.utils import QuerysetRelatedMixin


class RalphRelatedField(QuerysetRelatedMixin, relations.PrimaryKeyRelatedField):
    pass


class RalphHyperlinkedRelatedField(
    QuerysetRelatedMixin, relations.HyperlinkedRelatedField
):
    pass
