#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from lck.django.common.models import TimeTrackable, WithConcurrentGetOrCreate
from lck.django.choices import Choices


class CI_RELATION_TYPES(Choices):
    _ = Choices.Choice

    CONTAINS = _('Contains')
    REQUIRES = _('Requires')
    HASROLE =_('Has role')

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

contenttype_mappings={
        'discovery.device' : 'dd',
}

class CIContentTypePrefix(TimeTrackable):
    content_type_name = models.CharField(max_length=255, null=False, primary_key=True)
    prefix = models.SlugField()

    @classmethod
    def get_prefix_by_object(cls, content_object, fallback=None):
        content_type=ContentType.objects.get_for_model(content_object)
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
                obj = CIContentTypePrefix.objects.get(content_type_name='%s.%s' % (
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



class CILayer(TimeTrackable):
    name = models.SlugField()

    def __unicode__(self):
        return " %s " %  self.name

class CIRelation(TimeTrackable):
    class Meta:
        unique_together = ('parent', 'child', 'type')
    readonly = models.BooleanField(default=False, null = False)
    parent = models.ForeignKey('CI', related_name='parent',
            verbose_name=_("Parent"))
    child = models.ForeignKey('CI', related_name='child',
            verbose_name=_("Child"))

    type  = models.IntegerField(max_length=11, choices=CI_RELATION_TYPES(),
            verbose_name=_("relation kind"))

    def __unicode__(self):
        return "%s | %s | -> %s " %  (
                self.parent,
                self.type,
                self.child,
        )

    def save(self, user=None, *args, **kwargs):
        self.saving_user = user
        return super(CIRelation, self).save(*args, **kwargs)



class CIType(TimeTrackable):
    name = models.SlugField()

    def __unicode__(self):
        return "%s" %  self.name

class CIAttribute(TimeTrackable):
    name = models.CharField(max_length = 100, verbose_name=_("Name"))
    attribute_type = models.IntegerField(
            max_length=11,
            choices=CI_ATTRIBUTE_TYPES(),
            verbose_name=_("attribute kind"))

    choices = models.CharField(
            max_length = 1024,
            null=True,
            blank=True,
            verbose_name = _("options"),
    )

    ci_types = models.ManyToManyField(CIType)

    def __unicode__(self):
        return "%s (%s)" %  (self.name, self.get_attribute_type_display())

    def clean(self):
        validation_msg = 'Options: Invalid format! Valid  example is: 1.Option one|2.Option two'
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
    value = models.DateField(verbose_name=_("value"), null = True, blank=True)

    def __unicode__(self):
        return "%s" %  self.value


class CIValueInteger(TimeTrackable):
    value = models.IntegerField(verbose_name=_("value"), null = True, blank=True)

    def __unicode__(self):
            return "%s" %  self.value

class CIValueFloat(TimeTrackable):
    value = models.FloatField(
            verbose_name=_("value"),
            null = True,
            blank=True,
    )

    def __unicode__(self):
            return "%s" %  self.value

class CIValueString(TimeTrackable):
    value = models.CharField(
            max_length = 1024,
            verbose_name=_("value"),
            null=True,
            blank=True,
            )

    def __unicode__(self):
            return "%s" %  self.value


class CIValueChoice(TimeTrackable):
    value = models.IntegerField(
            verbose_name=_("value"),
            null = True,
            blank=True,
            )

    def __unicode__(self):
            return "%s" %  self.value


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
    business_service = models.BooleanField(verbose_name=_("Business service"),
            default=False)
    technical_service = models.BooleanField(verbose_name=_("Technical service"),
            default=True)
    pci_scope = models.BooleanField(
            default=False,
    )
    layers = models.ManyToManyField(CILayer,
            verbose_name=_("layers containing given CI") )
    barcode = models.CharField(verbose_name=_("barcode"), max_length=255,
        unique=True, null=True, default=None)
    content_type = models.ForeignKey(ContentType,
            verbose_name=_("content type"),
            null = True,
            blank = True,
    )
    object_id = models.PositiveIntegerField(
            verbose_name=_("object id"),
            null=True,
            blank=True,
    )
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    state = models.IntegerField(max_length=11, choices=CI_STATE_TYPES(),
            default=CI_STATE_TYPES.INACTIVE.id, verbose_name=_("state")  )
    status  = models.IntegerField(max_length=11, choices=CI_STATUS_TYPES(),
            default=CI_STATUS_TYPES.REFERENCE.id, verbose_name=_("status")  )
    type = models.ForeignKey(CIType)
    zabbix_id = models.CharField(
        null = True,
        blank = True,
        max_length=30,
    )
    relations = models.ManyToManyField("self", symmetrical=False,
            through='CIRelation')
    added_manually = models.BooleanField(default=False)
    owners = models.ManyToManyField('CIOwner',
            through='CIOwnership',
            verbose_name=_("configuration item owners"))

    class Meta:
        unique_together = ('content_type', 'object_id')

    def __unicode__(self):
        return "%s (%s)" %  (self.name, self.type)

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
            return list([unicode(x)
                for x in self.content_object.venture.technical_owners()])
        elif self.content_object and self.type.id == CI_TYPES.VENTURE.id:
            return list([unicode(x)
                for x in self.content_object.technical_owners() ] or ['-'])
        else:
            return ['-']

    @classmethod
    def get_by_content_object(self, content_object):
        # find CI using his content object
        prefix = CIContentTypePrefix.get_prefix_by_object(content_object, None)
        if not prefix:
            # fixtures not loaded, or content type not registered in CMDB. Skip checking.
            return None
        try:
            ci = CI.objects.get(uid='%s-%s' % (prefix, content_object.id))
        except CI.DoesNotExist:
            ci = None
        return ci

    @models.permalink
    def get_absolute_url(self):
        return "/cmdb/ci/view/%i" % self.id

    def save(self, user=None, *args, **kwargs):
        self.saving_user = user
        return super(CI, self).save(*args, **kwargs)


class CIAttributeValue(TimeTrackable):
    ci = models.ForeignKey('CI')
    attribute = models.ForeignKey(CIAttribute)

    """ Only one of three fk's below can be used for storing
    data according to type used """
    value_integer = models.ForeignKey(CIValueInteger,
            null = True,
            blank = True,
            verbose_name=_("integer value "))
    value_string = models.ForeignKey(CIValueString,
            null = True,
            blank = True,
            verbose_name=_("string value"))
    value_date = models.ForeignKey(CIValueDate,
            null = True,
            blank = True,
            verbose_name=_("date value"))
    value_float = models.ForeignKey(CIValueFloat,
            null = True,
            blank = True,
            verbose_name=_("float value"))
    value_choice = models.ForeignKey(CIValueChoice,
            null = True,
            blank = True,
            verbose_name=_("choice value"))


class CIOwnershipType(Choices):
    _ = Choices.Choice

    technical = _("technical owner")
    business = _("business owner")


class CIOwnership(TimeTrackable):
    ci = models.ForeignKey('CI')
    owner = models.ForeignKey('CIOwner')
    type = models.PositiveIntegerField(verbose_name=_("type of ownership"),
        choices=CIOwnershipType(), default=CIOwnershipType.technical.id)

    def __unicode__(self):
        return '%s is %s of %s ' % (self.owner, self.get_type_display(), self.ci )


class CIOwner(TimeTrackable, WithConcurrentGetOrCreate):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True)

    class Meta:
        verbose_name = _("configuration item owner")
        verbose_name_plural = _("configuration item owners")

    def __unicode__(self):
        return ' '.join([self.first_name, self.last_name])


