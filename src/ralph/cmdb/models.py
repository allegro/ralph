#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from lck.django.choices import Choices

class CI_RELATION_TYPES(Choices):
    _ = Choices.Choice

    CONTAINS = _(u'Contains')
    REQUIRES = _( u'Requires')
    HASROLE =_(u'Has role')

class CI_STATE_TYPES(Choices):
    _ = Choices.Choice

    ACTIVE = _(u'Active')
    INACTIVE = _(u'Inactive')
    WAITING = _(u'Waiting')

class CI_STATUS_TYPES(Choices):
    _ = Choices.Choice

    CHANGED = _( u'Changed')
    REFERENCE = _( u'Reference')

class CI_ATTRIBUTE_TYPES(Choices):
    _ = Choices.Choice

    INTEGER=_('Integer')
    STRING=_('String')
    DATE=_('Date')
    FLOAT=_('Real')
    CHOICE=_('Choice List')

class CI_CHANGE_TYPES(Choices):
    _ = Choices.Choice

    CONF_GIT=_('Git Configuration')
    CONF_AGENT=_('Services reconfiguration')
    DEVICE=_('Device attribute change')
    ZABBIX_TRIGGER=_('Zabbix trigger')
    STATUSOFFICE=_('Status office service change')


class CI_CHANGE_PRIORITY_TYPES(Choices):
    _ = Choices.Choice

    NOTICE = _('Notice')
    WARNING = _('Warning')
    ERROR = _('Error')
    CRITICAL = _('Critical')


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


class CIContentTypePrefix(models.Model):
    content_type_name = models.CharField(max_length=255, null=False, primary_key=True)
    prefix = models.SlugField()

    @classmethod
    def get_prefix_by_object(cls, content_object):
        content_type=ContentType.objects.get_for_model(content_object)
        return CIContentTypePrefix.objects.get(content_type_name='%s.%s' % (
                content_type.app_label,
                content_type.model,
                ))

    def get_content_type(self):
        app, model = self.content_type_name.split('.')
        return ContentType.objects.get_by_natural_key(app, model)


class CILayer(models.Model):
    name = models.SlugField()

    def __unicode__(self):
        return " %s " %  self.name

class CIRelation(models.Model):
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

class CIType(models.Model):
    name = models.SlugField()

    def __unicode__(self):
        return "%s" %  self.name

class CIAttribute(models.Model):
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
        if self.choices:
            try:
                len_checks = min([ len(x.split('.'))==2 and
                    x.split('.')[0].strip()
                    and x.split('.')[1].strip()
                    for x in self.choices.split('|')])
                if not len_checks:
                    raise ValidationError(validation_msg)
            except Exception,e:
                    raise ValidationError(validation_msg)


class CIValueDate(models.Model):
    value = models.DateField(verbose_name=_("value"), null = True, blank=True)

    def __unicode__(self):
        return "%s" %  self.value



class CIValueInteger(models.Model):
    value = models.IntegerField(verbose_name=_("value"), null = True, blank=True)

    def __unicode__(self):
            return "%s" %  self.value

class CIValueFloat(models.Model):
    value = models.FloatField(
            verbose_name=_("value"),
            null = True,
            blank=True,
    )

    def __unicode__(self):
            return "%s" %  self.value

class CIValueString(models.Model):
    value = models.CharField(
            max_length = 1024,
            verbose_name=_("value"),
            null=True,
            blank=True,
            )

    def __unicode__(self):
            return "%s" %  self.value

class CIValueChoice(models.Model):
    value = models.IntegerField(
            verbose_name=_("value"),
            null = True,
            blank=True,
            )

    def __unicode__(self):
            return "%s" %  self.value

class CIChangeZabbixTrigger(models.Model):
    ci = models.ForeignKey('CI', null = True)
    trigger_id = models.IntegerField(max_length=11,null=False )
    host = models.CharField(max_length=255,null=False )
    host_id = models.IntegerField(max_length=11,null=False )
    status = models.IntegerField(max_length=11,null=False )
    priority = models.IntegerField(max_length=11,null=False )
    description = models.CharField(max_length=1024)
    lastchange = models.CharField(max_length=1024)
    comments = models.CharField(max_length=1024)

class CIChangeStatusOfficeIncident(models.Model):
    ci = models.ForeignKey('CI', null = True)
    time = models.DateTimeField()
    status = models.IntegerField(max_length=11,null=False )
    subject = models.CharField(max_length=1024)
    incident_id= models.IntegerField(max_length=11,null=False )

class CIChange(models.Model):
    ci = models.ForeignKey('CI', null = True, blank=True)
    type = models.IntegerField(max_length=11, choices=CI_CHANGE_TYPES(),
            null=False )
    priority = models.IntegerField(max_length=11,
            choices=CI_CHANGE_PRIORITY_TYPES(),
            null=False )
    content_type = models.ForeignKey(ContentType, verbose_name=_("content type"),
            null = True  )
    object_id = models.PositiveIntegerField(
            verbose_name=_("object id"),
            null=True,
            blank=True,
    )
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    time = models.DateTimeField()
    message = models.CharField(max_length=1024)

    @classmethod
    def get_by_content_object(cls, content_object):
        ct = ContentType.objects.get_for_model(content_object)
        return CIChange.objects.get(object_id=content_object.id,
                content_type=ct)


    class Meta:
        unique_together = ('content_type', 'object_id')


class CIChangeGit(models.Model):
    file_paths = models.CharField(max_length=3000, null = False)
    comment = models.CharField(max_length=1000, null = False)
    author = models.CharField(max_length = 200, null = False)
    changeset = models.CharField(max_length=80, null = False)

class CIChangePuppet(models.Model):
    ci = models.ForeignKey('CI',
            null=True,
            blank=True,
    )
    configuration_version = models.CharField(max_length=30)
    host = models.CharField(max_length=100)
    kind = models.CharField(max_length=30)
    time = models.DateTimeField()
    status = models.CharField(max_length=30)

class PuppetLog(models.Model):
    cichange = models.ForeignKey('CIChangePuppet')
    source = models.CharField(max_length=100)
    message =models.CharField(max_length=1024)
    tags = models.CharField(max_length=100)
    time = models.DateTimeField()
    level = models.CharField(max_length=100)

class PuppetResourceStatus(models.Model):
    cichange= models.ForeignKey('CIChangePuppet')
    change_count = models.IntegerField()
    changed = models.BooleanField()
    failed = models.BooleanField()
    skipped = models.BooleanField()
    file = models.CharField(max_length=1024)
    line = models.IntegerField()
    resource = models.CharField(max_length=300)
    resource_type = models.CharField(max_length=300)
    time = models.DateTimeField()
    title = models.CharField(max_length=100)

class CI(models.Model):
    uid = models.CharField(
            max_length=100,
            verbose_name=_("CI UID"),
            null=True, blank=True,
    )
    # not required, since auto-save
    name = models.CharField(max_length=256, verbose_name=_("CI name"))
    # not required, since auto-save
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
            default=CI_STATE_TYPES.INACTIVE.id,verbose_name=_("state")  )
    status  = models.IntegerField(max_length=11, choices=CI_STATUS_TYPES(),
            default=CI_STATUS_TYPES.REFERENCE.id,verbose_name=_("status")  )
    type = models.ForeignKey(CIType)
    zabbix_id = models.CharField(
        null = True,
        blank = True,
        max_length=30,
    )
    relations = models.ManyToManyField("self", symmetrical=False,
            through='CIRelation')

    def __unicode__(self):
        return "%s" %  self.name

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
        prefix_record = CIContentTypePrefix.get_prefix_by_object(content_object)
        uid_prefix=prefix_record.prefix
        return CI.objects.get(uid='%s-%s' % (uid_prefix,content_object.id))

#    @models.permalink
#    def get_absolute_url(self):
#        return "/cmdb/ci/view/%i" % self.id

    class Meta:
        unique_together = ('content_type', 'object_id')

class CIAttributeValue(models.Model):
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

class CIEvent(models.Model):
    ''' Abstract for CIProblem/CIIncident '''
    ci = models.ForeignKey('CI',
            null = True,
            blank = True,
    )
    time = models.DateTimeField()
    summary = models.CharField(max_length=1024)
    description = models.CharField(max_length=1024)
    jira_id = models.CharField(max_length=100)
    status = models.CharField(max_length=300)
    assignee = models.CharField(max_length=300)

    class Meta:
        abstract = True

class CIProblem(CIEvent):
    pass

class CIIncident(CIEvent):
    pass


