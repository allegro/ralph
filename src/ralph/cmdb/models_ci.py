#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools as it

from dj.choices.fields import ChoiceField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from lck.django.common.models import TimeTrackable, WithConcurrentGetOrCreate
from lck.django.choices import Choices
from pygraph.classes.digraph import digraph
from pygraph.algorithms.cycles import find_cycle


class CI_RELATION_TYPES(Choices):
    _ = Choices.Choice

    CONTAINS = _('Contains')
    REQUIRES = _('Requires')
    HASROLE = _('Has role')


class CI_STATE_TYPES(Choices):
    _ = Choices.Choice

    ACTIVE = _('Active')
    INACTIVE = _('Inactive')
    WAITING = _('Waiting for deactivation')


class CI_STATUS_TYPES(Choices):
    _ = Choices.Choice

    CHANGED = _('Changed')
    REFERENCE = _('Reference')


class CI_ATTRIBUTE_TYPES(Choices):
    _ = Choices.Choice

    INTEGER = _('Integer')
    STRING = _('String')
    DATE = _('Date')
    FLOAT = _('Real')
    CHOICE = _('Choice List')


# Constants from  db
# see fixtures/0_types.yaml
class CI_TYPES(Choices):
    _ = Choices.Choice

    APPLICATION = _('Application')
    DEVICE = _('Device')
    PROCEDURE = _('Procedure')
    VENTURE = _('Venture')
    VENTUREROLE = _('Venture Role')
    BUSINESSLINE = _('Business Line')
    SERVICE = _('Service')
    NETWORK = _('Network')
    DATACENTER = _('Data Center')
    NETWORKTERMINATOR = _('Network Terminator')


contenttype_mappings = {
    'discovery.device': 'dd',
}


class CIContentTypePrefix(TimeTrackable):
    content_type_name = models.CharField(
        max_length=255, null=False, primary_key=True)
    prefix = models.SlugField()

    @classmethod
    def get_prefix_by_object(cls, content_object, fallback=None):
        content_type = ContentType.objects.get_for_model(content_object)
        label = '%s.%s' % (
            content_type.app_label,
            content_type.model,
        )
        first_run = contenttype_mappings.get(label)
        if first_run:
            # dict lookup
            return first_run
        else:
            # fixtures lookup
            try:
                obj = CIContentTypePrefix.objects.get(
                    content_type_name='%s.%s' % (
                        content_type.app_label,
                        content_type.model,
                    ))
            except CIContentTypePrefix.DoesNotExist:
                if fallback:
                    return fallback
                raise
            return obj.prefix

    def get_content_type(self):
        app, model = self.content_type_name.split('.')
        return ContentType.objects.get_by_natural_key(app, model)


class CIType(TimeTrackable):
    name = models.SlugField()
    icon_class = models.CharField(
        max_length=100,
        help_text="""The 'fugue'
            icons are installed and recommended. Search them at:
            <a href="http://p.yusukekamiyamane.com/icons/search/fugue/">
                http://p.yusukekamiyamane.com/icons/search/fugue/
            </a>
            If you need other icons, you need to edit CSS files.
        """,
        null=False,
        blank=False,
    )

    def __unicode__(self):
        return "%s" % self.name


class CILayerIcon(Choices):
    _ = Choices.Choice

    fugue_applications_blue = _('fugue-applications-blue')
    fugue_database = _('fugue-database')
    fugue_blue_documents = _('fugue-blue-documents')
    fugue_books_brown = _('fugue-books-brown')
    fugue_processor = _('fugue-processor')
    fugue_network_ip = _('fugue-network-ip')
    fugue_disc_share = _('fugue-disc-share')
    fugue_computer_network = _('fugue-computer-network')


class CILayer(TimeTrackable):
    # to save compatibility with SlugField from Django 1.3 and don't broke
    # migration in SQLite...
    name = models.CharField(max_length=50, db_index=True)
    connected_types = models.ManyToManyField(
        CIType,
        verbose_name=_('CI type'),
        blank=True,
    )
    icon = ChoiceField(
        verbose_name=_('icon'),
        choices=CILayerIcon,
        default=None,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('CI layer')
        verbose_name_plural = _('CI layers')
        ordering = ('name',)

    def __unicode__(self):
        return " %s " % self.name


class CIRelation(TimeTrackable, WithConcurrentGetOrCreate):

    class Meta:
        unique_together = ('parent', 'child', 'type')
    readonly = models.BooleanField(default=False, null=False)
    parent = models.ForeignKey(
        'CI', related_name='parent', verbose_name=_("Parent"))
    child = models.ForeignKey(
        'CI', related_name='child', verbose_name=_("Child"))

    type = models.IntegerField(
        max_length=11, choices=CI_RELATION_TYPES(),
        verbose_name=_("relation kind")
    )

    def __unicode__(self):
        return "%s | %s | -> %s " % (
            self.parent,
            self.type,
            self.child,
        )

    def clean(self):
        if not (self.parent_id and self.child_id):
            return
        validation_msg = 'CI can not have relation with himself'
        if self.parent == self.child:
            raise ValidationError(validation_msg)

    def save(self, user=None, *args, **kwargs):
        self.saving_user = user
        return super(CIRelation, self).save(*args, **kwargs)


class CIAttribute(TimeTrackable):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    attribute_type = models.IntegerField(
        max_length=11,
        choices=CI_ATTRIBUTE_TYPES(),
        verbose_name=_("attribute kind"))

    choices = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name=_("options"),
    )

    ci_types = models.ManyToManyField(CIType)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.get_attribute_type_display())

    def clean(self):
        validation_msg = (
            'Options: Invalid format! Valid  example is: 1.Option one|2.'
            'Option two'
        )

        def valid_chunk(chunk):
            try:
                prefix, suffix = chunk.split('.', 1)
            except ValueError:
                return False
            return bool(prefix.strip() and suffix.strip())
        if self.choices:
            if not all(valid_chunk(chunk)
                       for chunk in self.choices.split('|')):
                raise ValidationError(validation_msg)


class CIValueDate(TimeTrackable):
    value = models.DateField(
        verbose_name=_("value"), null=True, blank=True)

    def __unicode__(self):
        return "%s" % self.value


class CIValueInteger(TimeTrackable):
    value = models.IntegerField(
        verbose_name=_("value"), null=True, blank=True)

    def __unicode__(self):
        return "%s" % self.value


class CIValueFloat(TimeTrackable):
    value = models.FloatField(
        verbose_name=_("value"),
        null=True,
        blank=True,
    )

    def __unicode__(self):
        return "%s" % self.value


class CIValueString(TimeTrackable):
    value = models.CharField(
        max_length=1024,
        verbose_name=_("value"),
        null=True,
        blank=True,
    )

    def __unicode__(self):
        return "%s" % self.value


class CIValueChoice(TimeTrackable):
    value = models.IntegerField(
        verbose_name=_("value"),
        null=True,
        blank=True,
    )

    def __unicode__(self):
        return "%s" % self.value


class CI(TimeTrackable):
    uid = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("CI UID"),
        null=True,
        blank=True,
    )
    # not required, since auto-save
    name = models.CharField(max_length=256, verbose_name=_("CI name"))
    business_service = models.BooleanField(
        verbose_name=_("Business service"), default=False,
    )
    technical_service = models.BooleanField(
        verbose_name=_("Technical service"), default=True,
    )
    pci_scope = models.BooleanField(default=False)
    layers = models.ManyToManyField(
        CILayer, verbose_name=_("layers containing given CI")
    )
    barcode = models.CharField(
        verbose_name=_("barcode"), max_length=255, unique=True, null=True,
        default=None,
    )
    content_type = models.ForeignKey(
        ContentType, verbose_name=_("content type"), null=True, blank=True,
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_("object id"),
        null=True,
        blank=True,
    )
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    state = models.IntegerField(
        max_length=11, choices=CI_STATE_TYPES(),
        default=CI_STATE_TYPES.INACTIVE.id, verbose_name=_("state"),
    )
    status = models.IntegerField(
        max_length=11, choices=CI_STATUS_TYPES(),
        default=CI_STATUS_TYPES.REFERENCE.id, verbose_name=_("status"),
    )
    type = models.ForeignKey(CIType)
    zabbix_id = models.CharField(
        null=True,
        blank=True,
        max_length=30,
    )
    relations = models.ManyToManyField(
        "self", symmetrical=False, through='CIRelation')
    added_manually = models.BooleanField(default=False)
    owners = models.ManyToManyField(
        'CIOwner', through='CIOwnership',
        verbose_name=_("configuration item owners"),
    )

    @property
    def url(self):
        return '/cmdb/ci/view/{0}'.format(self.id)

    @classmethod
    def get_duplicate_names(cls):
        dupes = cls.objects.values('name').distinct().annotate(
            models.Count('id'),
        ).filter(id__count__gt=1)
        cis = cls.objects.filter(
            name__in=[dupe['name'] for dupe in dupes],
        ).order_by('name')
        # If I try to return the groupby itself the groups are empty
        for name, cis in it.groupby(cis, lambda x: x.name):
            yield name, list(cis)

    class Meta:
        unique_together = ('content_type', 'object_id')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.type)

    @classmethod
    def get_uid_by_content_object(cls, obj):
        prefix = CIContentTypePrefix.get_prefix_by_object(obj, '')
        return '%s-%s' % (prefix, obj.id)

    def get_jira_display(self):
        return "%(name)s %(uid)s - #%(barcode)s type: %(type)s" % (
            dict(
                name=self.name,
                uid=self.uid,
                barcode=self.barcode or '',
                type=self.type
            )
        )

    def get_service(self):
        """
        Business / Organisation Unit Layer
            Venture 1->
                Venture 2->
                    Venture Role ->
                        Host ->
        Iterate upside, stop on first Venture in Business Layer
        """

    def get_technical_owners(self):
        if self.content_object and getattr(
                self.content_object, 'venture', None):
            return list([
                unicode(x) for x in
                self.content_object.venture.technical_owners()] or ['-'])
        elif self.content_object and self.type.id == CI_TYPES.VENTURE.id:
            return list([
                unicode(x) for x in self.content_object.technical_owners()
            ] or ['-'])
        else:
            return ['-']

    @classmethod
    def get_cycle(cls):
        allci = CI.objects.all().values('pk')
        relations = CIRelation.objects.all().values('parent_id', 'child_id')
        cis = [x['pk'] for x in allci]
        rel = [(x['parent_id'], x['child_id']) for x in relations]
        cycle = cls.has_cycle(cis, rel)
        return cycle

    @classmethod
    def has_cycle(cls, nodes, edges):
        gr = digraph()
        gr.add_nodes(nodes)
        for edge in edges:
            gr.add_edge(edge)
        return find_cycle(gr)

    @classmethod
    def get_by_content_object(self, content_object):
        # find CI using his content object
        prefix = CIContentTypePrefix.get_prefix_by_object(content_object, None)
        if not prefix:
            # fixtures not loaded, or content type not registered in CMDB.
            # Skip checking.
            return None
        try:
            ci = CI.objects.get(uid='%s-%s' % (prefix, content_object.id))
        except CI.DoesNotExist:
            ci = None
        return ci

    def get_absolute_url(self):
        return reverse('ci_view', kwargs={'ci_id': self.id})

    def save(self, user=None, *args, **kwargs):
        self.saving_user = user
        return super(CI, self).save(*args, **kwargs)

    def _get_related(self, self_field, other_field):
        """Iterate over the related objects.
        :param first_field: The field on relation that points to this CI
        :param second_field: The field on relation that points to other CI
        """
        for relation in getattr(self, self_field).all():
            yield getattr(relation, other_field)

    def get_parents(self):
        return self._get_related(self_field='child', other_field='parent')

    def get_children(self):
        return self._get_related(self_field='parent', other_field='child')

    @property
    def icon(self):
        return self.type.icon_class


class CIAttributeValue(TimeTrackable):
    ci = models.ForeignKey('CI')
    attribute = models.ForeignKey(CIAttribute)

    """ Only one of three fk's below can be used for storing
    data according to type used """
    value_integer = models.ForeignKey(
        CIValueInteger, null=True, blank=True,
        verbose_name=_("integer value "),
    )
    value_string = models.ForeignKey(
        CIValueString, null=True, blank=True, verbose_name=_("string value"),
    )
    value_date = models.ForeignKey(
        CIValueDate, null=True, blank=True, verbose_name=_("date value"),
    )
    value_float = models.ForeignKey(
        CIValueFloat, null=True, blank=True, verbose_name=_("float value")
    )

    value_choice = models.ForeignKey(
        CIValueChoice, null=True, blank=True, verbose_name=_("choice value"),
    )

    TYPE_FIELDS_VALTYPES = {
        CI_ATTRIBUTE_TYPES.INTEGER.id: ('value_integer', CIValueInteger),
        CI_ATTRIBUTE_TYPES.STRING.id: ('value_string', CIValueString),
        CI_ATTRIBUTE_TYPES.FLOAT.id: ('value_float', CIValueFloat),
        CI_ATTRIBUTE_TYPES.DATE.id: ('value_date', CIValueDate),
        CI_ATTRIBUTE_TYPES.CHOICE.id: ('value_choice', CIValueChoice),
    }

    @property
    def value(self):
        """The property that find the "right" CIValueX."""
        value_field, _ = self.TYPE_FIELDS_VALTYPES[
            self.attribute.attribute_type
        ]
        value_object = getattr(self, value_field)
        if value_object is None:
            return
        return value_object.value

    @value.setter
    def value(self, value):
        value_field, ValueType = self.TYPE_FIELDS_VALTYPES[
            self.attribute.attribute_type
        ]
        val = ValueType(value=value)
        val.save()
        setattr(self, value_field, val)
        self.save()


class CIOwnershipType(Choices):
    _ = Choices.Choice

    technical = _("technical owner")
    business = _("business owner")


class CIOwnership(TimeTrackable):
    ci = models.ForeignKey('CI')
    owner = models.ForeignKey('CIOwner')
    type = models.PositiveIntegerField(
        verbose_name=_("type of ownership"), choices=CIOwnershipType(),
        default=CIOwnershipType.technical.id,
    )

    def __unicode__(self):
        return '%s is %s of %s ' % (
            self.owner, self.get_type_display(), self.ci,
        )


class CIOwnershipManager(models.Manager):

    """The manager of owners. The django manager interface is required by
    tastypie to correctly handle m2m relations."""

    def __init__(self, descriptor, inst):
        self.descriptor = descriptor
        self.own_type = self.descriptor.own_type
        self.inst = inst

    def get_query_set(self):
        return self.inst.owners.filter(ciownership__type=self.own_type)

    def clear(self):
        self.descriptor.__delete__(self.inst)

    def add(self, *owners):
        self.descriptor._add(self.inst, owners)


class CIOwnershipDescriptor(object):

    """Descriptor simplifying the access to CI owners."""

    def __init__(self, own_type):
        self.own_type = own_type

    def __get__(self, inst, cls):
        if inst is None:
            return self
        return CIOwnershipManager(self, inst)

    def _add(self, inst, owners):
        for owner in owners:
            own = CIOwnership(ci=inst, owner=owner, type=self.own_type)
            own.save()

    def __set__(self, inst, owners):
        self.__delete__(inst)
        self._add(inst, owners)

    def __delete__(self, inst):
        CIOwnership.objects.filter(ci=inst, type=self.own_type).delete()


CI.business_owners = CIOwnershipDescriptor(CIOwnershipType.business.id)
CI.technical_owners = CIOwnershipDescriptor(CIOwnershipType.technical.id)


class CIOwner(TimeTrackable, WithConcurrentGetOrCreate):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True)
    sAMAccountName = models.CharField(max_length=256, blank=True)

    def __unicode__(self):
        return ' '.join([self.first_name, self.last_name])
